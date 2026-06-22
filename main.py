import json
import os
import unicodedata
from typing import Any, Dict, List, Optional

import mailer

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, NumericProperty, StringProperty
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.fitimage import FitImage
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.textfield import MDTextField

import api_client as db

APP_VERSION = "1.0.0"


def _parse_version(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0, 0, 0)


class UpdateScreen(Screen):
    message = StringProperty("")
    download_url = StringProperty("")
    is_force_update = BooleanProperty(False)

    def on_pre_enter(self):
        if self.is_force_update:
            self.ids.update_title.text = "Mise à jour requise"
            self.ids.update_desc.text = self.message or "Une version plus récente est requise pour continuer."
            self.ids.later_btn.opacity = 0
            self.ids.later_btn.disabled = True
            self.ids.quit_btn.opacity = 1
            self.ids.quit_btn.disabled = False
        else:
            self.ids.update_title.text = "Nouvelle version disponible"
            self.ids.update_desc.text = self.message or "Une mise à jour est disponible."
            self.ids.later_btn.opacity = 1
            self.ids.later_btn.disabled = False
            self.ids.quit_btn.opacity = 0
            self.ids.quit_btn.disabled = True

    def do_update(self):
        if self.download_url:
            import webbrowser
            webbrowser.open(self.download_url)
        else:
            self.ids.update_desc.text = "Aucune URL de téléchargement configurée. Contactez le support."

    def do_later(self):
        app = App.get_running_app()
        app.root.current = "login"

    def do_quit(self):
        App.get_running_app().stop()


class LoginScreen(Screen):
    message = StringProperty("")

    def do_login(self) -> None:
        email = self.ids.login_email.text.strip()
        password = self.ids.login_password.text.strip()
        ok, msg, user = db.login_user(email, password)
        self.message = msg
        if ok and user:
            if user["role"] != "client":
                self.message = "Cette application est reservee aux comptes clients."
                return
            app = App.get_running_app()
            app.current_user = user
            app.route_after_login()
        elif not ok and msg == "VERIFICATION_REQUIRED":
            app = App.get_running_app()
            app.pending_user_id = user["id"]
            self.message = "Email non verifie. Un code vous a ete envoye."
            # Renvoyer le code via le serveur
            code = db.resend_verification_code(app.pending_user_id)
            if not code:
                self.message = "Erreur lors de l'envoi du code"
                return
            app.pending_code = code
            mailer.send_verification_code(user["email"], code)
            app.root.current = "verify_email"
            Clock.schedule_once(lambda dt: setattr(app, "pending_code", None), 120)

    def clear_fields(self) -> None:
        self.ids.login_email.text = ""
        self.ids.login_password.text = ""


class SignupScreen(Screen):
    message = StringProperty("")

    def do_signup(self) -> None:
        full_name = self.ids.sign_name.text.strip()
        email = self.ids.sign_email.text.strip()
        password = self.ids.sign_password.text.strip()
        if not full_name or not email or not password:
            self.message = "Tous les champs sont obligatoires."
            return
        ok, msg = db.create_user(full_name, email, password, "client")
        self.message = msg
        if ok:
            self.ids.sign_name.text = ""
            self.ids.sign_email.text = ""
            self.ids.sign_password.text = ""

_SIGNUP_SCREENS = (
    "signup_step1",
    "signup_step2",
    "signup_step3",
    "signup_step5",
    "signup_step6",
)


class SignupStep1Screen(Screen):
    message = StringProperty("")

    def validate_step1(self) -> None:
        self.message = ""
        name = self.ids.step1_name.text.strip()
        if not name:
            self.message = "Le nom est obligatoire."
            return
        if not self.ids.gender_homme.active and not self.ids.gender_femme.active and not self.ids.gender_autre.active:
            self.message = "Veuillez selectionner un genre."
            return
        day = self.ids.birth_day.text.strip()
        month = self.ids.birth_month.text.strip()
        year = self.ids.birth_year.text.strip()
        try:
            d, m, y = int(day), int(month), int(year)
        except ValueError:
            self.message = "Date de naissance invalide (JJ, MM, AAAA)."
            return
        if not (1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100):
            self.message = "Date de naissance invalide."
            return
        gender = (
            "homme"
            if self.ids.gender_homme.active
            else "femme"
            if self.ids.gender_femme.active
            else "autre"
        )
        app = App.get_running_app()
        app.signup_draft["full_name"] = name
        app.signup_draft["birth_day"] = day
        app.signup_draft["birth_month"] = month
        app.signup_draft["birth_year"] = year
        app.signup_draft["gender"] = gender
        self.manager.current = "signup_step2"


class SignupStep2Screen(Screen):
    message = StringProperty("")

    def go_back(self) -> None:
        idx = _SIGNUP_SCREENS.index(self.name)
        if idx > 0:
            self.manager.current = _SIGNUP_SCREENS[idx - 1]

    def validate_step2(self) -> None:
        self.message = ""
        email = self.ids.step2_email.text.strip()
        address = self.ids.step2_address.text.strip()
        if not email or "@" not in email:
            self.message = "Email invalide."
            return
        if not address:
            self.message = "L'adresse est obligatoire."
            return
        app = App.get_running_app()
        app.signup_draft["email"] = email
        app.signup_draft["address"] = address
        self.manager.current = "signup_step3"


class SignupStep3Screen(Screen):
    message = StringProperty("")

    def go_back(self) -> None:
        idx = _SIGNUP_SCREENS.index(self.name)
        if idx > 0:
            self.manager.current = _SIGNUP_SCREENS[idx - 1]

    def toggle_password_field(self, field_name: str, btn: Any) -> None:
        w = self.ids[field_name]
        w.password = not w.password
        btn.icon = "eye-off" if w.password else "eye"

    @staticmethod
    def _password_text(field) -> str:
        # TextInput stocke le vrai texte dans _lines ; avec KivyMD + mode mot de passe,
        # .text peut parfois etre desynchronise. NFC harmonise les caracteres Unicode.
        if getattr(field, "_lines", None):
            raw = "".join(field._lines)
        else:
            raw = field.text or ""
        raw = raw.replace("\r", "").replace("\n", "").strip()
        return unicodedata.normalize("NFC", raw)

    def validate_step3(self) -> None:
        self.message = ""
        p1 = self._password_text(self.ids.step3_password)
        p2 = self._password_text(self.ids.step3_confirm_password)
        if len(p1) < 6:
            self.message = "Le mot de passe doit faire au moins 6 caracteres."
            return
        if p1 != p2:
            self.message = "Les mots de passe ne correspondent pas."
            return
        App.get_running_app().signup_draft["password"] = p1
        self.manager.current = "signup_step5"


class SignupStep5Screen(Screen):
    message = StringProperty("")

    def on_pre_enter(self, *args: Any) -> None:
        d = App.get_running_app().signup_draft
        self.ids.recap_text.text = (
            f"Nom: {d.get('full_name', '—')}\n"
            f"Naissance: {d.get('birth_day', '')}/{d.get('birth_month', '')}/{d.get('birth_year', '')}\n"
            f"Genre: {d.get('gender', '—')}\n"
            f"Email: {d.get('email', '—')}\n"
            f"Adresse: {d.get('address', '—')}"
        )

    def go_back(self) -> None:
        idx = _SIGNUP_SCREENS.index(self.name)
        if idx > 0:
            self.manager.current = _SIGNUP_SCREENS[idx - 1]

    def validate_step5(self) -> None:
        self.manager.current = "signup_step6"


class SignupStep6Screen(Screen):
    message = StringProperty("")
    privacy_accepted = BooleanProperty(False)
    terms_accepted = BooleanProperty(False)

    TERMS_TEXT = """
Conditions d'Utilisation
Dernière mise à jour : 15/04/2026

1. Introduction
Les présentes Conditions d'Utilisation régissent l'utilisation de l'application mobile Spaceness fournie par Spaceness. En utilisant l'Application, vous acceptez de vous conformer aux présentes conditions.

2. Accès et utilisation de l'Application
- Eligibilité : Vous devez avoir au moins 18 ans pour utiliser cette Application.
- Licence d'utilisation : Nous vous octroyons une licence limitée, non exclusive et non transférable.
- Interdictions : Vous vous engagez à ne pas utiliser l'Application pour des activités illégales ou frauduleuses.

3. Comptes utilisateur
- Création de compte : Vous devrez fournir des informations personnelles véridiques.
- Responsabilité du compte : Vous êtes responsable de la sécurité de votre compte.
- Suspension ou résiliation : Nous nous réservons le droit de suspendre votre compte en cas de violation.

4. Paiements et Transactions
L'Application peut proposer des transactions financières. Vous acceptez de respecter toutes les politiques de paiement.

5. Propriété intellectuelle
Tous les droits de propriété intellectuelle relatifs à l'Application sont détenus par Spaceness.

6. Modifications des Conditions
Nous nous réservons le droit de modifier les présentes conditions à tout moment.

7. Limitation de responsabilité
Nous ne serons pas responsables des dommages directs, indirects ou accessoires.

8. Loi applicable
Les présentes conditions sont régies par la législation en vigueur.
"""

    PRIVACY_TEXT = """
Politique de Confidentialité
Dernière mise à jour : 15/04/2026

1. Introduction
La présente Politique de Confidentialité décrit comment Spaceness recueille, utilise et protège vos informations personnelles.

2. Informations que nous recueillons
- Informations d'identification : nom, adresse e-mail, numéro de téléphone, adresse.
- Informations de paiement : informations bancaires pour effectuer des transactions.
- Données d'utilisation : informations sur la manière dont vous utilisez l'Application.

3. Comment nous utilisons vos informations
Nous utilisons les informations collectées pour :
- Fournir, exploiter et améliorer l'Application.
- Vous envoyer des informations importantes et des notifications.
- Traiter vos transactions financières.
- Répondre à vos demandes et fournir une assistance client.

4. Partage de vos informations
Nous ne partageons vos informations personnelles qu'avec nos partenaires et autorités compétentes si requis par la loi.

5. Protection de vos informations
Nous mettons en œuvre des mesures de sécurité appropriées pour protéger vos informations personnelles.

6. Vos droits
Vous avez le droit de :
- Accéder, corriger ou supprimer vos informations personnelles.
- Retirer votre consentement à tout moment.
- Demander des informations sur les données que nous collectons.

7. Cookies
Nous utilisons des cookies pour améliorer votre expérience et analyser l'utilisation.

8. Modifications
Nous nous réservons le droit de modifier cette politique. Toute modification sera publiée sur cette page.

9. Contact
Pour toute question, contactez-nous via l'Application.
"""

    def show_terms_popup(self) -> None:
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        
        content = BoxLayout(orientation="vertical", padding=dp(10), size_hint_y=None, height=dp(500))
        scroll = ScrollView(size_hint_y=1, do_scroll_y=True)
        
        text_label = Label(
            text=self.TERMS_TEXT.replace('\n', '\n\n'),
            text_size=(dp(320), None),
            size_hint_y=None,
            height=dp(1200),
            font_size="13sp",
            halign="left",
            valign="top",
            color=(0.1, 0.1, 0.1, 1)
        )
        
        scroll.add_widget(text_label)
        content.add_widget(scroll)
        
        dlg = MDDialog(
            title="Conditions d'Utilisation",
            type="custom",
            content_cls=content,
            size_hint=(0.95, 0.8),
            buttons=[
                MDFlatButton(text="Fermer", on_release=lambda *x: dlg.dismiss())
            ]
        )
        dlg.open()

    def show_privacy_popup(self) -> None:
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        
        content = BoxLayout(orientation="vertical", padding=dp(10), size_hint_y=None, height=dp(500))
        scroll = ScrollView(size_hint_y=1, do_scroll_y=True)
        
        text_label = Label(
            text=self.PRIVACY_TEXT.replace('\n', '\n\n'),
            text_size=(dp(320), None),
            size_hint_y=None,
            height=dp(1200),
            font_size="13sp",
            halign="left",
            valign="top",
            color=(0.1, 0.1, 0.1, 1)
        )
        
        scroll.add_widget(text_label)
        content.add_widget(scroll)
        
        dlg = MDDialog(
            title="Politique de Confidentialité",
            type="custom",
            content_cls=content,
            size_hint=(0.95, 0.8),
            buttons=[
                MDFlatButton(text="Fermer", on_release=lambda *x: dlg.dismiss())
            ]
        )
        dlg.open()

    def go_back(self) -> None:
        idx = _SIGNUP_SCREENS.index(self.name)
        if idx > 0:
            self.manager.current = _SIGNUP_SCREENS[idx - 1]

    def validate_step6(self) -> None:
        self.message = ""
        if not self.privacy_accepted or not self.terms_accepted:
            self.message = "Vous devez accepter les deux politiques."
            return
        app = App.get_running_app()
        d = app.signup_draft
        full_name = str(d.get("full_name", "")).strip()
        email = str(d.get("email", "")).strip()
        password = str(d.get("password", ""))
        ok, msg = db.create_user(full_name, email, password, "client")
        self.message = msg
        if not ok:
            return
        app.loading_message = "Envoi du code de verification..."
        app.root.current = "loading"
        Clock.schedule_once(lambda dt: self._send_verification(app, email, password), 0.3)

    def _send_verification(self, app, email, password):
        ok_login, msg_login, user = db.login_user(email, password)
        if not ok_login and msg_login == "VERIFICATION_REQUIRED":
            app.pending_user_id = user["id"]
            code = db.resend_verification_code(app.pending_user_id)
            if not code:
                self.message = "Erreur lors de la generation du code de verification"
                app.root.current = "signup_step6"
                return
            sent, err = mailer.send_verification_code(email, code)
            if not sent:
                self.message = f"Compte cree mais echec envoi email: {err}"
                app.root.current = "signup_step6"
                return
            app.pending_code = code
            app.signup_draft.clear()
            app.root.current = "verify_email"
            Clock.schedule_once(lambda dt: setattr(app, "pending_code", None), 120)
        else:
            self.message = "Erreur inattendue lors de la creation du compte."
            app.root.current = "signup_step6"


class ForgotPasswordScreen(Screen):
    message = StringProperty("")

    def send_reset_code(self) -> None:
        self.message = ""
        email = self.ids.forgot_email.text.strip()
        if not email:
            self.message = "Veuillez entrer votre adresse email."
            return
        app = App.get_running_app()
        app.loading_message = "Envoi du code de reinitialisation..."
        app.root.current = "loading"
        Clock.schedule_once(lambda dt: self._do_send_code(app, email), 0.3)

    def _do_send_code(self, app, email):
        ok, msg = db.forgot_password(email)
        if not ok:
            self.message = msg
            app.root.current = "forgot_password"
            return
        code = msg
        app.pending_reset_email = email
        app.pending_code = code
        sent, err = mailer.send_verification_code(email, code)
        app.root.current = "reset_password"

class ResetPasswordScreen(Screen):
    message = StringProperty("")

    def on_pre_enter(self):
        self.ids.reset_code.text = ""
        self.ids.reset_password.text = ""
        self.ids.reset_confirm.text = ""
        self.message = ""
        app = App.get_running_app()
        if hasattr(app, "pending_code") and app.pending_code:
            self.ids.reset_code.text = ""

    def reset_password(self) -> None:
        self.message = ""
        code = self.ids.reset_code.text.strip()
        password = self.ids.reset_password.text.strip()
        confirm = self.ids.reset_confirm.text.strip()
        if len(code) != 6 or not code.isdigit():
            self.message = "Entrez le code a 6 chiffres recu par email."
            return
        if not password or len(password) < 6:
            self.message = "Le mot de passe doit faire au moins 6 caracteres."
            return
        if password != confirm:
            self.message = "Les mots de passe ne correspondent pas."
            return
        app = App.get_running_app()
        email = getattr(app, "pending_reset_email", "")
        if not email:
            self.message = "Session expiree. Recommencez."
            return
        ok, msg = db.reset_password(email, code, password)
        if not ok:
            self.message = msg
            return
        app.pending_reset_email = None
        app.pending_code = None
        self.message = "Mot de passe reinitialise ! Connectez-vous."
        Clock.schedule_once(lambda dt: setattr(app.root, "current", "login"), 2)

class VerificationScreen(Screen):
    message = StringProperty("")
    can_resend = BooleanProperty(True)

    def on_pre_enter(self) -> None:
        self.ids.code_input.text = ""
        self.message = ""
        self.can_resend = True
        app = App.get_running_app()
        if hasattr(app, "pending_code") and app.pending_code:
            self.ids.debug_code_label.text = f"Code de test: {app.pending_code}"
        else:
            self.ids.debug_code_label.text = ""

    def verify_code(self) -> None:
        app = App.get_running_app()
        user_id = app.pending_user_id
        if not user_id:
            self.message = "Session expiree. Reconnectez-vous."
            return
        code = self.ids.code_input.text.strip()
        if len(code) != 6 or not code.isdigit():
            self.message = "Entrez un code a 6 chiffres."
            return
        ok, msg = db.verify_email_code(user_id, code)
        self.message = msg
        if ok:
            user = db.get_user_by_id(user_id)
            if user:
                app.current_user = user
                app.pending_user_id = None
                app.route_after_login()

    def resend_code(self) -> None:
        if not self.can_resend:
            return
        app = App.get_running_app()
        user_id = app.pending_user_id
        if not user_id:
            self.message = "Session expiree."
            return
        user = db.get_user_by_id(user_id)
        if not user:
            self.message = "Utilisateur introuvable."
            return
        code = db.resend_verification_code(user_id)
        if not code:
            self.message = "Erreur lors de l'envoi du code"
            return
        app.pending_code = code
        sent, err = mailer.send_verification_code(user["email"], code)
        if sent:
            self.message = "Nouveau code envoye par email."
            self.can_resend = False
            self.ids.debug_code_label.text = f"Code de test: {code}"
            Clock.schedule_once(lambda dt: setattr(self, "can_resend", True), 30)
        else:
            self.message = f"Erreur d'envoi: {err}"


class ProductCard(BoxLayout):
    product_id = NumericProperty(0)
    shop_id = NumericProperty(0)
    title = StringProperty("")
    subtitle = StringProperty("")
    description = StringProperty("")
    price = StringProperty("")
    image_url = StringProperty("")
    stock_text = StringProperty("")
    show_shop_link = BooleanProperty(True)
    is_favorite = BooleanProperty(False)


class MarketScreen(Screen):
    message = StringProperty("")
    user_header = StringProperty("")

    def on_pre_enter(self) -> None:
        app = App.get_running_app()
        user = app.current_user or {}
        self.user_header = user.get("full_name", "Utilisateur") or "Utilisateur"
        app.check_notifications()
        self.refresh_products()

    def refresh_products(self) -> None:
        app = App.get_running_app()
        rows = db.list_market_products(search="", category="")
        container = self.ids.market_products
        container.clear_widgets()
        for row in rows:
            is_fav = False
            if app.current_user:
                is_fav = db.is_favorite(app.current_user["id"], row["id"])
            card = ProductCard(
                product_id=row["id"],
                shop_id=row["shop_id"],
                title=f"{row['name']} ({row['category']})",
                subtitle=f"{row['shop_name']}",
                description=row["description"] or "-",
                price=f"{row['price']:.2f} cr",
                image_url=row["image_url"] or "",
                stock_text=f"Stock: {row['stock']}",
                is_favorite=is_fav,
            )
            container.add_widget(card)
        self.message = f"{len(rows)} produit(s)"

    def go_to_search(self) -> None:
        q = self.ids.market_search_bar.text.strip()
        App.get_running_app().open_search_screen(q)

    def open_shop(self, shop_id: int) -> None:
        App.get_running_app().open_shop(shop_id)

    def toggle_drawer(self) -> None:
        drawer = self.ids.market_drawer
        if drawer.state == "open":
            drawer.set_state("close")
        else:
            drawer.set_state("open")

    def close_drawer(self) -> None:
        self.ids.market_drawer.set_state("close")

    def nav_to_market(self) -> None:
        self.close_drawer()
        self.refresh_products()

    def nav_to_cart(self) -> None:
        self.close_drawer()
        App.get_running_app().open_cart()

    def nav_logout(self) -> None:
        self.close_drawer()
        App.get_running_app().logout()


class SearchScreen(Screen):
    message = StringProperty("")
    filter_dialog: Optional[MDDialog] = None

    def on_pre_enter(self, *args: Any) -> None:
        app = App.get_running_app()
        self.ids.search_field.text = app.search_value
        self.refresh_results()

    def refresh_results(self) -> None:
        app = App.get_running_app()
        search = app.search_value.strip()
        category = app.category_value.strip()
        rows = db.list_market_products(search=search, category=category)
        container = self.ids.search_products
        container.clear_widgets()
        for row in rows:
            is_fav = False
            if app.current_user:
                is_fav = db.is_favorite(app.current_user["id"], row["id"])
            card = ProductCard(
                product_id=row["id"],
                shop_id=row["shop_id"],
                title=f"{row['name']} ({row['category']})",
                subtitle=f"{row['shop_name']}",
                description=row["description"] or "-",
                price=f"{row['price']:.2f} cr",
                image_url=row["image_url"] or "",
                stock_text=f"Stock: {row['stock']}",
                is_favorite=is_fav,
            )
            container.add_widget(card)
        self.message = f"{len(rows)} produit(s) trouvé(s)"
        try:
            empty_state = self.ids.empty_state
            empty_state.opacity = 1 if len(rows) == 0 else 0
        except Exception:
            pass

    def go_back(self) -> None:
        """Retourne au market et efface la recherche"""
        App.get_running_app().search_value = ""
        self.ids.search_field.text = ""
        App.get_running_app().root.current = "market"

    def on_search_text(self, text: str) -> None:
        """Met à jour la recherche en temps réel"""
        App.get_running_app().search_value = text
        self.refresh_results()

    def apply_search_bar(self) -> None:
        app = App.get_running_app()
        app.search_value = self.ids.search_field.text.strip()
        self.refresh_results()

    def open_filters(self) -> None:
        app = App.get_running_app()
        if self.filter_dialog is None:
            content = Factory.FilterDialogContent()
            self.filter_dialog = MDDialog(
                title="Filtres de recherche",
                type="custom",
                auto_dismiss=False,
                content_cls=content,
                buttons=[
                    MDFlatButton(text="Annuler", on_release=lambda *_: self.filter_dialog.dismiss()),
                    MDFlatButton(text="Appliquer", on_release=lambda *_: self.apply_filters()),
                ],
            )
        content = self.filter_dialog.content_cls
        content.ids.f_search.text = app.search_value
        content.ids.f_category.text = app.category_value
        content.ids.f_qty.text = app.qty_value
        self.filter_dialog.open()

    def apply_filters(self) -> None:
        if self.filter_dialog is None:
            return
        app = App.get_running_app()
        content = self.filter_dialog.content_cls
        app.search_value = content.ids.f_search.text.strip()
        app.category_value = content.ids.f_category.text.strip()
        app.qty_value = content.ids.f_qty.text.strip() or "1"
        self.ids.search_field.text = app.search_value
        self.filter_dialog.dismiss()
        self.refresh_results()

    def back_to_market(self) -> None:
        App.get_running_app().root.current = "market"


class ShopScreen(Screen):
    message = StringProperty("")
    shop_data = DictProperty({})
    is_subscribed = BooleanProperty(False)

    def load_shop(self, shop_id: int) -> None:
        details = db.get_shop_details(shop_id)
        if not details:
            self.message = "Boutique introuvable."
            return
        self.shop_data = dict(details)
        details_dict = dict(details)
        self.ids.shop_profile_name.text = details_dict["shop_name"]
        self.ids.shop_name_header.text = details_dict["shop_name"]
        self.ids.shop_logo.source = details_dict.get("logo_url") or "img/logo.png"
        self.ids.shop_banner.source = details_dict.get("banner_url") or "img/placeholder_banner.png"
        self.ids.shop_desc.text = details_dict["description"] or "-"
        
        subscriber_count = db.get_shop_subscriber_count(shop_id)
        self.ids.subscriber_count.text = f"{subscriber_count} abonné{'s' if subscriber_count > 1 else ''}"
        
        app = App.get_running_app()
        if app.current_user:
            self.is_subscribed = db.is_subscribed_to_shop(app.current_user["id"], shop_id)
            self.update_subscribe_button()
        
        self.refresh_products()
    
    def update_subscribe_button(self) -> None:
        """Met à jour le texte et la couleur du bouton d'abonnement"""
        btn = self.ids.subscribe_btn
        if self.is_subscribed:
            btn.text = "Abonné"
            btn.md_bg_color = (0.2, 0.8, 0.4, 1)  # Vert
            btn.text_color = (1, 1, 1, 1)  # Blanc
        else:
            btn.text = "S'abonner"
            btn.md_bg_color = (0.13, 0.59, 0.95, 1)  # Bleu
            btn.text_color = (1, 1, 1, 1)  # Blanc
    
    def toggle_subscription(self) -> None:
        """Bascule l'abonnement à la boutique"""
        app = App.get_running_app()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        
        shop_id = self.shop_data.get("id")
        if not shop_id:
            return
        
        user_id = app.current_user["id"]
        
        if self.is_subscribed:
            # Se désabonner
            if db.unsubscribe_from_shop(user_id, shop_id):
                self.is_subscribed = False
                self.message = "Désabonnement réussi"
        else:
            # S'abonner
            if db.subscribe_to_shop(user_id, shop_id):
                self.is_subscribed = True
                self.message = "Abonnement réussi ! Vous verrez les articles de cette boutique en priorité"
        
        self.update_subscribe_button()
        Clock.schedule_once(lambda dt: setattr(self, "message", ""), 3)

    def refresh_products(self) -> None:
        shop_id = self.shop_data.get("id")
        if not shop_id:
            return
        rows = db.list_shop_products(shop_id)
        container = self.ids.shop_products
        container.clear_widgets()
        for row in rows:
            card = ProductCard(
                product_id=row["id"],
                shop_id=shop_id,
                title=f"{row['name']} ({row['category']})",
                subtitle=f"Stock: {row['stock']} | {'Actif' if row['is_active'] else 'Inactif'}",
                description=row["description"] or "-",
                price=f"{row['price']:.2f} credits",
                image_url=row["image_url"] or "",
                stock_text=f"Stock: {row['stock']}",
                show_shop_link=False,
            )
            container.add_widget(card)


class ProductDetailsScreen(Screen):
    message = StringProperty("")
    product_id = NumericProperty(0)

    def load_product(self, product_id: int) -> None:
        row = db.get_product_by_id(product_id)
        if not row:
            self.message = "Produit introuvable."
            return
        self.product_id = row["id"]
        
        img1 = row["image_url"] or ""
        img2 = row["image_url_2"] if "image_url_2" in row.keys() else ""
        img3 = row["image_url_3"] if "image_url_3" in row.keys() else ""
        
        default_img = "img/placeholder_product.png"
        
        self.ids.d_image.source = img1 if img1 else default_img
        self.ids.d_image.opacity = 1 if img1 else 0
        
        if img2:
            self.ids.d_image_2.source = img2
            self.ids.d_image_2.opacity = 1
        else:
            self.ids.d_image_2.source = default_img
            self.ids.d_image_2.opacity = 0
        
        if img3:
            self.ids.d_image_3.source = img3
            self.ids.d_image_3.opacity = 1
        else:
            self.ids.d_image_3.source = default_img
            self.ids.d_image_3.opacity = 0
        
        self.ids.d_title.text = row["name"]
        self.ids.d_shop.text = f"Boutique: {row['shop_name']}"
        self.ids.d_category.text = f"Categorie: {row['category']}"
        self.ids.d_price.text = f"{row['price']:.2f} credits"
        self.ids.d_stock.text = f"Stock disponible: {row['stock']}"
        self.ids.d_desc.text = row["description"] or "-"
        
        avg_rating, review_count = db.get_product_rating(product_id)
        self.ids.d_rating.text = f"{avg_rating}"
        self.ids.d_rating_count.text = f"({review_count} avis)"
        
        self.load_reviews()
        self.message = ""
    
    def load_reviews(self) -> None:
        container = self.ids.reviews_container
        for child in list(container.children):
            if child.id != "no_reviews":
                container.remove_widget(child)
        
        reviews = db.get_product_reviews(self.product_id)
        try:
            no_reviews_label = self.ids.reviews_container.ids.get("no_reviews")
            if no_reviews_label:
                no_reviews_label.opacity = 1 if not reviews else 0
        except Exception:
            pass
        
        for review in reviews:
            review_card = MDCard(
                orientation="vertical",
                padding=dp(10),
                spacing=dp(4),
                size_hint_y=None,
                height=dp(80),
                md_bg_color=(0.97, 0.98, 1, 1),
            )
            stars = "★" * review["rating"] + "☆" * (5 - review["rating"])
            review_card.add_widget(MDLabel(text=f"{review['user_name']}  {stars}", bold=True, font_size="12sp", size_hint_y=None, height=dp(22)))
            review_card.add_widget(MDLabel(text=review["comment"] or "Sans commentaire", theme_text_color="Secondary", font_size="11sp", size_hint_y=None, height=dp(36)))
            review_card.add_widget(MDLabel(text=review["created_at"][:10], theme_text_color="Hint", font_size="10sp", size_hint_y=None, height=dp(18)))
            container.add_widget(review_card)
    
    def open_review_dialog(self) -> None:
        app = App.get_running_app()
        if not app.current_user or app.current_user["role"] != "client":
            self.message = "Connectez-vous pour laisser un avis"
            return
        
        if hasattr(self, '_review_dialog') and self._review_dialog is not None:
            self._review_dialog.dismiss()
        
        content = Factory.ReviewDialogContent()
        content.ids.review_rating.bind(value=lambda instance, value: setattr(content.ids.rating_label, 'text', f"{int(value)} / 5"))
        
        self._review_dialog = MDDialog(
            title="Laisser un avis",
            type="custom",
            auto_dismiss=False,
            content_cls=content,
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda *_: self._review_dialog.dismiss()),
                MDRaisedButton(text="Envoyer", on_release=lambda *_: self._submit_review(content)),
            ],
        )
        self._review_dialog.open()
    
    def _submit_review(self, content) -> None:
        app = App.get_running_app()
        rating = int(content.ids.review_rating.value)
        comment = content.ids.review_comment.text.strip()
        db.add_review(app.current_user["id"], self.product_id, rating, comment)
        avg_rating, review_count = db.get_product_rating(self.product_id)
        self.ids.d_rating.text = f"{avg_rating}"
        self.ids.d_rating_count.text = f"({review_count} avis)"
        self.load_reviews()
        self._review_dialog.dismiss()
    
    def on_carousel_change(self) -> None:
        pass

    def request_add_to_cart(self) -> None:
        app = App.get_running_app()
        if app.current_user["role"] != "client":
            self.message = "Seul un client peut ajouter au panier."
            return
        qty_text = self.ids.d_qty.text.strip() or "1"
        try:
            qty = int(qty_text)
        except ValueError:
            self.message = "Quantite invalide."
            return
        app.show_add_to_cart_dialog(self.product_id, qty)


class CartScreen(Screen):
    message = StringProperty("")

    def on_pre_enter(self) -> None:
        self.refresh_cart()

    def refresh_cart(self) -> None:
        app = App.get_running_app()
        container = self.ids.cart_items
        container.clear_widgets()
        total = 0.0
        if not app.cart:
            empty_card = MDCard(
                orientation="vertical",
                padding=dp(24),
                size_hint_y=None,
                height=dp(180),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
            )
            empty_card.add_widget(MDIcon(icon="cart-outline", font_size=dp(60), theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={"center_x": 0.5}))
            empty_card.add_widget(MDLabel(text="Votre panier est vide", theme_text_color="Secondary", font_style="Subtitle1", halign="center", size_hint_y=None, height=dp(30)))
            empty_card.add_widget(MDLabel(text="Ajoutez des articles pour commencer", theme_text_color="Hint", font_size="12sp", halign="center", size_hint_y=None, height=dp(24)))
            container.add_widget(empty_card)
            self.ids.cart_total.text = "Total: 0.00 credits"
            return
        for item in app.cart:
            line_total = item["price"] * item["qty"]
            total += line_total
            card = MDCard(
                orientation="horizontal",
                padding=dp(10),
                spacing=dp(12),
                size_hint_y=None,
                height=dp(120),
                radius=[12, 12, 12, 12],
                elevation=2,
                md_bg_color=(1, 1, 1, 1),
            )
            img_src = item.get("image_url") or "img/placeholder_product.png"
            card.add_widget(
                FitImage(
                    source=img_src,
                    size_hint=(None, None),
                    size=(dp(100), dp(100)),
                    radius=[8, 8, 8, 8],
                )
            )
            info = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_x=1)
            info.add_widget(
                Label(
                    text=item["name"],
                    size_hint_y=None,
                    height=dp(24),
                    font_size="14sp",
                    bold=True,
                    color=(0.1, 0.1, 0.1, 1),
                    text_size=(None, None),
                    halign="left",
                    valign="middle",
                )
            )
            info.add_widget(
                Label(
                    text=item.get("shop_name", "Boutique"),
                    size_hint_y=None,
                    height=dp(18),
                    font_size="11sp",
                    color=(0.5, 0.5, 0.5, 1),
                    halign="left",
                )
            )
            info.add_widget(
                Label(
                    text=f"{item['price']:.2f} cr x {item['qty']}",
                    size_hint_y=None,
                    height=dp(18),
                    font_size="12sp",
                    color=(0.4, 0.4, 0.4, 1),
                    halign="left",
                )
            )
            info.add_widget(
                Label(
                    text=f"Sous-total: {line_total:.2f} cr",
                    size_hint_y=None,
                    height=dp(22),
                    bold=True,
                    color=(0.13, 0.59, 0.95, 1),
                    halign="left",
                )
            )
            card.add_widget(info)
            pid = int(item["product_id"])
            actions = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(44), spacing=dp(4))
            btn_del = MDIconButton(icon="trash-can-outline", theme_text_color="Error", on_release=lambda *_a, p=pid: self.remove_line(p))
            btn_det = MDIconButton(icon="eye-outline", theme_text_color="Primary", on_release=lambda *_a, p=pid: App.get_running_app().open_product_details(p))
            actions.add_widget(btn_del)
            actions.add_widget(btn_det)
            card.add_widget(actions)
            container.add_widget(card)
        self.ids.cart_total.text = f"Total: {total:.2f} credits"

    def remove_line(self, product_id: int) -> None:
        App.get_running_app().remove_cart_item(product_id)
        self.refresh_cart()

    def clear_cart(self) -> None:
        app = App.get_running_app()
        app.cart = []
        app.update_cart_badge()
        self.message = "Panier vide."
        self.refresh_cart()

    def commander(self) -> None:
        App.get_running_app().show_commande_confirm_dialog()


class OrdersScreen(Screen):
    message = StringProperty("")

    def on_pre_enter(self) -> None:
        self.refresh_orders()

    def refresh_orders(self) -> None:
        app = App.get_running_app()
        container = self.ids.client_orders
        container.clear_widgets()
        if not app.current_user or app.current_user["role"] != "client":
            self.message = "Ecran reserve aux clients."
            return
        rows = db.list_orders_for_client(app.current_user["id"])
        if not rows:
            empty_card = MDCard(
                orientation="vertical",
                padding=dp(24),
                size_hint_y=None,
                height=dp(180),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
            )
            empty_card.add_widget(MDIcon(icon="clipboard-text-outline", font_size=dp(60), theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={"center_x": 0.5}))
            empty_card.add_widget(MDLabel(text="Aucune commande", theme_text_color="Secondary", font_style="Subtitle1", halign="center", size_hint_y=None, height=dp(30)))
            empty_card.add_widget(MDLabel(text="Vos commandes apparaîtront ici", theme_text_color="Hint", font_size="12sp", halign="center", size_hint_y=None, height=dp(24)))
            container.add_widget(empty_card)
            return
        for row in rows:
            card = MDCard(
                orientation="horizontal",
                padding=dp(12),
                spacing=dp(12),
                size_hint_y=None,
                height=dp(130),
                radius=[12, 12, 12, 12],
                elevation=2,
                md_bg_color=(1, 1, 1, 1),
            )
            img_src = row["product_image_url"] or "img/placeholder_product.png"
            card.add_widget(
                FitImage(
                    source=img_src,
                    size_hint=(None, None),
                    size=(dp(100), dp(100)),
                    radius=[8, 8, 8, 8],
                )
            )
            info = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_x=1)
            info.add_widget(
                MDLabel(
                    text=f"Commande #{row['id']}",
                    bold=True,
                    font_size="13sp",
                    size_hint_y=None,
                    height=dp(22),
                )
            )
            info.add_widget(
                Label(
                    text=row["product_name"],
                    size_hint_y=None,
                    height=dp(20),
                    font_size="12sp",
                    bold=True,
                    color=(0.1, 0.1, 0.1, 1),
                    text_size=(None, None),
                    halign="left",
                    valign="middle",
                )
            )
            info.add_widget(
                Label(
                    text=f"{row['shop_name']}",
                    size_hint_y=None,
                    height=dp(18),
                    font_size="11sp",
                    color=(0.5, 0.5, 0.5, 1),
                    halign="left",
                )
            )
            info.add_widget(
                Label(
                    text=f"Qte: {row['quantity']} - {row['total_amount']:.2f} cr",
                    size_hint_y=None,
                    height=dp(18),
                    font_size="11sp",
                    color=(0.4, 0.4, 0.4, 1),
                    halign="left",
                )
            )
            status = row["status"]
            status_colors = {
                "pending": (0.9, 0.7, 0.1, 1),
                "confirmed": (0.13, 0.59, 0.95, 1),
                "shipped": (0.5, 0.3, 0.9, 1),
                "delivered": (0.2, 0.7, 0.3, 1),
                "cancelled": (0.8, 0.2, 0.2, 1)
            }
            status_color = status_colors.get(status.lower(), (0.5, 0.5, 0.5, 1))
            info.add_widget(
                MDLabel(
                    text=status.capitalize(),
                    theme_text_color="Custom",
                    text_color=status_color,
                    font_size="11sp",
                    bold=True,
                    size_hint_y=None,
                    height=dp(20),
                )
            )
            card.add_widget(info)
            pid = int(row["product_id"])
            actions = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(44), spacing=dp(4))
            btn_det = MDIconButton(icon="eye-outline", theme_text_color="Primary", on_release=lambda *_a, p=pid: App.get_running_app().open_product_details(p))
            btn_shop = MDIconButton(icon="store-outline", theme_text_color="Secondary", on_release=lambda *_a, s=int(row["shop_id"]): App.get_running_app().open_shop(s))
            actions.add_widget(btn_det)
            actions.add_widget(btn_shop)
            card.add_widget(actions)
            container.add_widget(card)
        self.message = f"{len(rows)} commande(s)."


class AccountScreen(Screen):
    message = StringProperty("")
    
    def on_pre_enter(self, *args: Any) -> None:
        print("DEBUG: AccountScreen.on_pre_enter() appelé")
        app = App.get_running_app()
        print(f"DEBUG: current_user = {app.current_user}")
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            print("DEBUG: Redirection vers login")
            Clock.schedule_once(lambda dt: setattr(app.root, "current", "login"), 1.5)
            return
        self.load_profile()
    
    def load_profile(self) -> None:
        print("DEBUG: load_profile() appelé")
        app = App.get_running_app()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            print("DEBUG: Pas de current_user")
            return
        user = db.get_user_by_id(app.current_user["id"])
        print(f"DEBUG: user récupéré = {user}")
        if user:
            print(f"DEBUG: Mise à jour des champs avec ids={self.ids.keys()}")
            self.ids.acc_name.text = user.get("full_name", "")
            self.ids.acc_email.text = user.get("email", "")
            self.ids.acc_phone.text = user.get("phone", "")
            self.ids.acc_address.text = user.get("address", "")
            self.ids.acc_birth_date.text = user.get("birth_date", "")
            self.ids.acc_gender.text = user.get("gender", "")
            # Mettre à jour l'en-tête
            self.ids.profile_name_header.text = user.get("full_name", "Utilisateur")
            self.ids.profile_email_header.text = user.get("email", "")
            print("DEBUG: Champs mis à jour avec succès")
        else:
            print("DEBUG: Utilisateur non trouvé en base")
    
    def save_profile(self) -> None:
        app = App.get_running_app()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        name = self.ids.acc_name.text.strip()
        phone = self.ids.acc_phone.text.strip()
        address = self.ids.acc_address.text.strip()
        if not name:
            self.message = "Le nom est obligatoire"
            return
        try:
            app.current_user["full_name"] = name
            self.message = "Profil mis à jour avec succès!"
        except Exception as e:
            self.message = f"Erreur: {str(e)}"


class ContactAdminScreen(Screen):
    message = StringProperty("")
    
    def on_pre_enter(self) -> None:
        self.refresh_messages()
        self._check_for_replies()
    
    def _check_for_replies(self) -> None:
        app = App.get_running_app()
        if not app.current_user:
            return
        messages = db.get_user_messages(app.current_user["id"])
        messages_dict = [dict(m) for m in messages]
        unread_notifications = [m for m in messages_dict if (m["is_from_admin"] or m["admin_reply"]) and not m["is_read"]]
        if unread_notifications:
            app.admin_notification = True
            self._show_reply_notification(len(unread_notifications))
            for msg in unread_notifications:
                db.mark_message_read(msg["id"])
        else:
            app.admin_notification = False
    
    def refresh_messages(self) -> None:
        app = App.get_running_app()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        container = self.ids.messages_container
        container.clear_widgets()
        
        messages = db.get_user_messages(app.current_user["id"])
        
        if not messages:
            empty = MDLabel(
                text="Aucun message. Utilisez le formulaire pour contacter l'administrateur.",
                theme_text_color="Secondary",
                halign="center",
                size_hint_y=None,
                height=dp(50)
            )
            container.add_widget(empty)
            return
        
        for msg in messages:
            card = MDCard(
                orientation="vertical",
                padding=dp(12),
                size_hint_y=None,
                height=dp(180),
                radius=[8, 8, 8, 8],
                md_bg_color=(0.97, 0.98, 1, 1) if not msg["admin_reply"] else (0.95, 1, 0.95, 1),
            )
            card.add_widget(MDLabel(
                text=f"[{msg['created_at'][:10]}] {msg['subject']}",
                bold=True,
                font_size="13sp",
                size_hint_y=None,
                height=dp(24)
            ))
            card.add_widget(MDLabel(
                text=msg["message"],
                theme_text_color="Secondary",
                font_size="12sp",
                size_hint_y=None,
                height=dp(40)
            ))
            if msg["admin_reply"]:
                card.add_widget(MDLabel(
                    text=f"Réponse admin: {msg['admin_reply']}",
                    theme_text_color="Custom",
                    text_color=(0.13, 0.59, 0.95, 1),
                    font_size="11sp",
                    bold=True,
                    size_hint_y=None,
                    height=dp(30)
                ))
            container.add_widget(card)
    
    def _show_reply_notification(self, count: int) -> None:
        msg_text = "nouvelle réponse" if count == 1 else f"{count} nouvelles réponses"
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton
        
        dlg = MDDialog(
            title="📩 Nouvelle réponse",
            text=f"L'administrateur vous a envoyé une {msg_text}!",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda *x: dlg.dismiss()
                )
            ]
        )
        dlg.open()
    
    def send_message(self) -> None:
        subject = self.ids.contact_subject.text.strip()
        message = self.ids.contact_message.text.strip()
        if not subject:
            self.message = "Le sujet est obligatoire"
            return
        if not message:
            self.message = "Le message est obligatoire"
            return
        app = App.get_running_app()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        
        success = db.send_admin_message(app.current_user["id"], subject, message)
        if success:
            self.message = "Message envoyé avec succès!"
            self.ids.contact_subject.text = ""
            self.ids.contact_message.text = ""
            self.refresh_messages()
        else:
            self.message = "Erreur lors de l'envoi du message"


class FavoritesScreen(Screen):
    message = StringProperty("")

    def on_pre_enter(self) -> None:
        self.refresh_favorites()

    def refresh_favorites(self) -> None:
        app = App.get_running_app()
        container = self.ids.favorites_grid
        container.clear_widgets()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        rows = db.list_favorites(app.current_user["id"])
        if not rows:
            empty_card = MDCard(
                orientation="vertical",
                padding=dp(24),
                size_hint_y=None,
                height=dp(180),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
            )
            empty_card.add_widget(MDIcon(icon="heart-outline", font_size=dp(60), theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={"center_x": 0.5}))
            empty_card.add_widget(MDLabel(text="Aucun favori", theme_text_color="Secondary", font_style="Subtitle1", halign="center", size_hint_y=None, height=dp(30)))
            empty_card.add_widget(MDLabel(text="Ajoutez des produits à vos favoris", theme_text_color="Hint", font_size="12sp", halign="center", size_hint_y=None, height=dp(24)))
            container.add_widget(empty_card)
            return
        for row in rows:
            card = ProductCard(
                product_id=row["id"],
                shop_id=row["shop_id"],
                title=row["name"],
                subtitle=row["shop_name"],
                price=f"{row['price']:.2f} cr",
                image_url=row["image_url"] or "",
                stock_text=f"Stock: {row['stock']}",
                is_favorite=True,
            )
            container.add_widget(card)
        self.message = f"{len(rows)} favori(s)"


class HistoryScreen(Screen):
    message = StringProperty("")

    def on_pre_enter(self) -> None:
        self.refresh_history()

    def refresh_history(self) -> None:
        app = App.get_running_app()
        container = self.ids.history_grid
        container.clear_widgets()
        if not app.current_user:
            self.message = "Veuillez vous connecter"
            return
        rows = db.list_history(app.current_user["id"])
        if not rows:
            empty_card = MDCard(
                orientation="vertical",
                padding=dp(24),
                size_hint_y=None,
                height=dp(180),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
            )
            empty_card.add_widget(MDIcon(icon="history", font_size=dp(60), theme_text_color="Custom", text_color=(0.6, 0.6, 0.6, 1), size_hint=(None, None), size=(dp(60), dp(60)), pos_hint={"center_x": 0.5}))
            empty_card.add_widget(MDLabel(text="Aucun historique", theme_text_color="Secondary", font_style="Subtitle1", halign="center", size_hint_y=None, height=dp(30)))
            empty_card.add_widget(MDLabel(text="Les produits vus apparaîtront ici", theme_text_color="Hint", font_size="12sp", halign="center", size_hint_y=None, height=dp(24)))
            container.add_widget(empty_card)
            return
        for row in rows:
            is_fav = False
            if app.current_user:
                is_fav = db.is_favorite(app.current_user["id"], row["id"])
            card = ProductCard(
                product_id=row["id"],
                shop_id=row["shop_id"],
                title=row["name"],
                subtitle=row["shop_name"],
                price=f"{row['price']:.2f} cr",
                image_url=row["image_url"] or "",
                stock_text=f"Stock: {row['stock']}",
                is_favorite=is_fav,
            )
            container.add_widget(card)
        self.message = f"{len(rows)} produit(s) vus"

    def clear_history(self) -> None:
        app = App.get_running_app()
        if not app.current_user:
            return
        db.clear_history(app.current_user["id"])
        self.message = "Historique effacé"
        self.refresh_history()


class RootManager(ScreenManager):
    pass


class LoadingScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        if app.loading_message == "Chargement...":
            Clock.schedule_once(self.finish_loading, 2)

    def finish_loading(self, dt):
        app = App.get_running_app()
        app.finish_loading()


class ShopMobileApp(MDApp):
    current_user: Optional[Dict[str, Any]] = None
    selected_shop_id: Optional[int] = None
    selected_product_id: Optional[int] = None
    cart: List[Dict[str, Any]] = []
    session_file = "session.json"
    signup_draft: Dict[str, Any] = {}
    search_value = StringProperty("")
    category_value = StringProperty("")
    qty_value = StringProperty("1")
    cart_badge_count = NumericProperty(0)
    _info_dialog: Optional[MDDialog] = None
    dark_mode = BooleanProperty(False)
    admin_notification = BooleanProperty(False)
    pending_user_id: Optional[int] = None
    pending_code: Optional[str] = None
    pending_reset_email: Optional[str] = None
    loading_message = StringProperty("Chargement...")

    def start_signup(self) -> None:
        self.signup_draft.clear()
        self.root.current = "signup_step1"

    def build(self):
        db.init_db()
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.title = "Spaceness - Marketplace"
        self.icon = "img/logo.png"
        root = Builder.load_file("app.kv")
        self._load_session()
        self.update_cart_badge()
        return root
    
    def on_start(self) -> None:
        self.root.current = "loading"
    
    def _retry_load_session(self, dt) -> None:
        if not self.current_user and os.path.exists(self.session_file):
            self._load_session()
        if self.current_user:
            self.route_after_login()
        else:
            self.root.current = "login"

    def finish_loading(self) -> None:
        settings = db.get_app_settings()
        if settings.get("is_blocked"):
            block_msg = settings.get("block_message", "L'application est actuellement en maintenance.")
            self._show_blocked_dialog(block_msg)
            return
        version_info = db.check_version()
        if version_info:
            current = _parse_version(APP_VERSION)
            min_v = _parse_version(version_info.get("min_version", "0.0.0"))
            latest_v = _parse_version(version_info.get("latest_version", "0.0.0"))
            if min_v > current:
                update_screen = self.root.get_screen("update")
                update_screen.message = version_info.get("update_message", "Une version plus récente est requise pour continuer. Veuillez télécharger la mise à jour.")
                update_screen.download_url = version_info.get("download_url", "")
                update_screen.is_force_update = True
                self.root.current = "update"
                return
            if latest_v > current:
                update_screen = self.root.get_screen("update")
                update_screen.message = version_info.get("update_message", "Une nouvelle version est disponible. Téléchargez-la pour profiter des dernières fonctionnalités.")
                update_screen.download_url = version_info.get("download_url", "")
                update_screen.is_force_update = False
                self.root.current = "update"
                return
        if self.current_user:
            self.route_after_login()
        else:
            Clock.schedule_once(self._retry_load_session, 1)
    
    def _show_blocked_dialog(self, message: str) -> None:
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton
        
        dlg = MDDialog(
            title="🔒 Application bloquée",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="Fermer",
                    on_release=lambda *x: self.stop()
                )
            ]
        )
        dlg._real_release_on_auto_dismiss_behavior = False
        dlg.open()
    
    def check_notifications(self) -> None:
        """Vérifie les notifications admin pour afficher le badge"""
        if not self.current_user:
            self.admin_notification = False
            return
        messages = db.get_user_messages(self.current_user["id"])
        messages_dict = [dict(m) for m in messages]
        unread_notifications = [m for m in messages_dict if (m["is_from_admin"] or m["admin_reply"]) and not m["is_read"]]
        self.admin_notification = len(unread_notifications) > 0
    
    def toggle_dark_mode(self) -> None:
        """Bascule entre le mode sombre et clair"""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"
        # Forcer la couleur du drawer à rester bleue foncée
        Clock.schedule_once(self._reset_drawer_color, 0.1)
    
    def _reset_drawer_color(self, dt):
        """Réinitialise la couleur du menu burger en bleu foncé"""
        try:
            market_screen = self.root.get_screen("market")
            drawer = market_screen.ids.market_drawer
            drawer.md_bg_color = (0.04, 0.11, 0.26, 1)
        except Exception:
            pass

    def route_after_login(self) -> None:
        if not self.current_user or self.current_user["role"] != "client":
            self.current_user = None
            self._clear_session()
            self.root.current = "login"
            return
        self.root.current = "market"
        self._save_session()

    def logout(self) -> None:
        self.current_user = None
        self.cart = []
        self.update_cart_badge()
        self.root.current = "login"
        self.root.get_screen("login").clear_fields()
        self._clear_session()

    def update_cart_badge(self) -> None:
        self.cart_badge_count = sum(int(x["qty"]) for x in self.cart)

    def open_search_screen(self, query: str = "") -> None:
        self.search_value = query.strip()
        self.root.current = "search"

    def open_shop(self, shop_id: int) -> None:
        self.selected_shop_id = shop_id
        shop_screen = self.root.get_screen("shop")
        shop_screen.load_shop(shop_id)
        self.root.current = "shop"

    def open_product_details(self, product_id: int) -> None:
        self.selected_product_id = product_id
        details_screen = self.root.get_screen("product_details")
        details_screen.load_product(product_id)
        if self.current_user:
            db.add_to_history(self.current_user["id"], product_id)
        self.root.current = "product_details"

    def toggle_favorite(self, product_id: int) -> None:
        if not self.current_user:
            return
        if db.is_favorite(self.current_user["id"], product_id):
            db.remove_from_favorites(self.current_user["id"], product_id)
        else:
            db.add_to_favorites(self.current_user["id"], product_id)
        self.refresh_current_screen()

    def refresh_current_screen(self) -> None:
        current = self.root.current
        if current == "market":
            self.root.get_screen("market").refresh_products()
        elif current == "search":
            self.root.get_screen("search").refresh_results()
        elif current == "favorites":
            self.root.get_screen("favorites").refresh_favorites()
        elif current == "history":
            self.root.get_screen("history").refresh_history()

    def show_add_to_cart_dialog(self, product_id: int, qty: int = 1) -> None:
        if not self.current_user or self.current_user["role"] != "client":
            return

        def confirm(*_a: Any) -> None:
            dlg.dismiss()
            ok, _msg = self.add_to_cart(product_id, qty)
            self.update_cart_badge()
            if ok:
                self._show_panier_info_dialog()

        dlg = MDDialog(
            type="simple",
            title="Panier",
            text="Ajouter cet article au panier ?",
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(text="Confirmer", on_release=confirm),
            ],
        )
        dlg.open()

    def _show_panier_info_dialog(self) -> None:
        if self._info_dialog:
            self._info_dialog.dismiss()
        dlg = MDDialog(
            type="simple",
            title="Article ajoute",
            text="Pour passer commande, ouvrez le panier via l'icone panier en haut a droite.",
            buttons=[MDRaisedButton(text="OK", on_release=lambda *_: dlg.dismiss())],
        )
        self._info_dialog = dlg
        dlg.open()

    def show_commande_confirm_dialog(self) -> None:
        if not self.cart:
            return
        if not self.current_user or self.current_user["role"] != "client":
            return

        def confirm(*_a: Any) -> None:
            dlg.dismiss()
            ok, msg = self._execute_checkout_orders()
            cart_screen = self.root.get_screen("cart")
            cart_screen.message = msg
            cart_screen.refresh_cart()
            self.update_cart_badge()
            if ok:
                self.root.current = "orders"
                self.root.get_screen("orders").refresh_orders()

        dlg = MDDialog(
            type="simple",
            title="Commander",
            text="Confirmer la commande ? Les articles seront enregistres dans Mes commandes.",
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(text="Confirmer", on_release=confirm),
            ],
        )
        dlg.open()

    def _execute_checkout_orders(self) -> tuple[bool, str]:
        if not self.cart:
            return False, "Panier vide."
        errors: List[str] = []
        success_count = 0
        for item in self.cart:
            ok, msg = db.place_order(self.current_user["id"], item["product_id"], item["qty"])
            if ok:
                success_count += 1
            else:
                errors.append(f"{item['name']}: {msg}")
        self.cart = []
        self.update_cart_badge()
        if errors:
            return False, f"{success_count} commande(s) ok. Erreurs: {' | '.join(errors[:2])}"
        return True, f"{success_count} commande(s) enregistree(s)."

    def remove_cart_item(self, product_id: int) -> None:
        self.cart = [x for x in self.cart if int(x["product_id"]) != int(product_id)]
        self.update_cart_badge()

    def add_to_cart(self, product_id: int, qty: int) -> tuple[bool, str]:
        if qty <= 0:
            return False, "Quantite invalide."
        row = db.get_product_by_id(product_id)
        if not row:
            return False, "Produit introuvable."
        if row["stock"] < qty:
            return False, "Stock insuffisant."
        for item in self.cart:
            if item["product_id"] == product_id:
                new_qty = item["qty"] + qty
                if new_qty > row["stock"]:
                    return False, "Stock insuffisant pour cette quantite."
                item["qty"] = new_qty
                return True, "Panier mis a jour."
        self.cart.append(
            {
                "product_id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "qty": qty,
                "image_url": row["image_url"] or "",
                "shop_name": row["shop_name"],
                "shop_id": int(row["shop_id"]),
            }
        )
        return True, "Ajoute au panier."

    def open_cart(self) -> None:
        self.root.current = "cart"

    def open_orders(self) -> None:
        self.root.current = "orders"

    def _save_session(self) -> None:
        if not self.current_user:
            return
        payload = {"user_id": self.current_user["id"]}
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def _load_session(self) -> None:
        if not os.path.exists(self.session_file):
            return
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            user_id = int(payload.get("user_id", 0))
        except Exception:
            return
        if not user_id:
            return
        try:
            user = db.get_user_by_id(user_id)
        except Exception:
            return
        if not user:
            self._clear_session()
            return
        if user["role"] != "client":
            self._clear_session()
            return
        if not user.get("is_verified"):
            self._clear_session()
            return
        self.current_user = user

    def _clear_session(self) -> None:
        if os.path.exists(self.session_file):
            os.remove(self.session_file)


if __name__ == "__main__":
    ShopMobileApp().run()
