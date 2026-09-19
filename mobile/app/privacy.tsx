import { StyleSheet, Text, View, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Spacing } from '@/constants/theme';

export default function PrivacyScreen() {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right', 'bottom']}>
      <ScreenHeader title="Politique de confidentialité" subtitle="Spaceness" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.date}>Dernière mise à jour : 15/04/2026</Text>

        <Text style={styles.title}>1. Introduction</Text>
        <Text style={styles.body}>
          La présente Politique de Confidentialité décrit comment Spaceness recueille, utilise et protège
          vos informations personnelles lorsque vous utilisez l'Application Spaceness. En utilisant
          l'Application, vous consentez à la collecte et à l'utilisation de vos informations conformément à
          cette politique.
        </Text>

        <Text style={styles.title}>2. Informations que nous recueillons</Text>
        <Text style={styles.body}>
          Nous collectons des informations personnelles que vous fournissez lors de la création de votre
          compte, telles que :
        </Text>
        <Text style={styles.bullet}>• Informations d'identification : nom, adresse e-mail, numéro de téléphone, adresse postale.</Text>
        <Text style={styles.bullet}>• Informations de paiement : informations bancaires et détails de paiement pour effectuer des transactions via l'Application.</Text>
        <Text style={styles.bullet}>• Données d'utilisation : informations sur la manière dont vous utilisez l'Application, telles que les actions que vous effectuez, les pages visitées et les interactions avec d'autres utilisateurs.</Text>

        <Text style={styles.title}>3. Comment nous utilisons vos informations</Text>
        <Text style={styles.body}>Nous utilisons les informations collectées pour :</Text>
        <Text style={styles.bullet}>• Fournir, exploiter et améliorer l'Application.</Text>
        <Text style={styles.bullet}>• Vous envoyer des informations importantes, y compris des mises à jour sur l'Application et des notifications de service.</Text>
        <Text style={styles.bullet}>• Traiter vos transactions financières et gérer vos paiements.</Text>
        <Text style={styles.bullet}>• Répondre à vos demandes et vous fournir une assistance client.</Text>

        <Text style={styles.title}>4. Partage de vos informations</Text>
        <Text style={styles.body}>Nous ne partageons vos informations personnelles qu'avec :</Text>
        <Text style={styles.bullet}>
          • Nos partenaires commerciaux et prestataires de services qui nous aident à exploiter
          l'Application, comme les services de paiement et de livraison.
        </Text>
        <Text style={styles.bullet}>
          • Les autorités compétentes, si cela est exigé par la loi, pour répondre à des demandes légales ou
          pour protéger nos droits.
        </Text>

        <Text style={styles.title}>5. Protection de vos informations</Text>
        <Text style={styles.body}>
          Nous mettons en œuvre des mesures de sécurité appropriées pour protéger vos informations
          personnelles contre l'accès, la divulgation, l'altération et la destruction non autorisés.
          Cependant, aucune méthode de transmission sur Internet ou de stockage électronique n'est 100 %
          sécurisée, et nous ne pouvons garantir une sécurité absolue.
        </Text>

        <Text style={styles.title}>6. Vos droits</Text>
        <Text style={styles.body}>Vous avez le droit de :</Text>
        <Text style={styles.bullet}>• Accéder, corriger ou supprimer vos informations personnelles.</Text>
        <Text style={styles.bullet}>• Retirer votre consentement à tout moment pour l'utilisation de vos données personnelles.</Text>
        <Text style={styles.bullet}>• Demander des informations sur les données que nous collectons à votre sujet.</Text>

        <Text style={styles.title}>7. Cookies et technologies similaires</Text>
        <Text style={styles.body}>
          Nous utilisons des cookies et des technologies similaires pour améliorer votre expérience
          d'utilisation de l'Application, pour analyser l'utilisation et pour personnaliser les contenus.
          Vous pouvez configurer votre navigateur pour refuser les cookies, mais cela pourrait affecter
          certaines fonctionnalités de l'Application.
        </Text>

        <Text style={styles.title}>8. Modifications de cette politique</Text>
        <Text style={styles.body}>
          Nous nous réservons le droit de modifier cette politique de confidentialité. Toute modification
          sera publiée sur cette page avec une date de mise à jour. Nous vous encourageons à consulter
          régulièrement cette politique.
        </Text>

        <Text style={styles.title}>9. Contact</Text>
        <Text style={styles.body}>
          Si vous avez des questions concernant cette politique de confidentialité, vous pouvez nous
          contacter à :
        </Text>
        <Text style={styles.bullet}>• spaceness15@gmail.com</Text>
        <Text style={styles.bullet}>• Lubumbashi / Kasanguku / Coin du Carmel</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.lg, paddingBottom: 48 },
  date: { fontSize: 13, color: Colors.textLight, marginBottom: 8 },
  title: { fontSize: 17, fontWeight: '800', color: Colors.text, marginTop: 22, marginBottom: 6 },
  sub: { fontSize: 14, fontWeight: '700', color: Colors.text, marginTop: 10, marginBottom: 3 },
  body: { fontSize: 14, lineHeight: 22, color: Colors.textSecondary },
  bullet: { fontSize: 14, lineHeight: 22, color: Colors.textSecondary, marginLeft: 8 },
});