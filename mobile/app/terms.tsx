import { StyleSheet, Text, View, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Spacing } from '@/constants/theme';

export default function TermsScreen() {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right', 'bottom']}>
      <ScreenHeader title="Conditions d'utilisation" subtitle="Spaceness" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.date}>Dernière mise à jour : 15/04/2026</Text>

        <Text style={styles.title}>1. Introduction</Text>
        <Text style={styles.body}>
          Les présentes Conditions d'Utilisation régissent l'utilisation de l'application mobile Spaceness
          fournie par Spaceness. En utilisant l'Application, vous acceptez de vous conformer aux présentes
          conditions. (Si vous n'acceptez pas ces conditions, vous ne devez pas utiliser l'Application.)
        </Text>

        <Text style={styles.title}>2. Accès et utilisation de l'Application</Text>
        <Text style={styles.sub}>Éligibilité :</Text>
        <Text style={styles.body}>
          Vous devez avoir au moins 18 ans pour utiliser cette Application. Si vous êtes mineur, vous devez
          obtenir le consentement de vos parents ou tuteurs avant d'utiliser l'Application.
        </Text>
        <Text style={styles.sub}>Licence d'utilisation :</Text>
        <Text style={styles.body}>
          Nous vous octroyons une licence limitée, non exclusive et non transférable pour utiliser
          l'Application sur vos appareils personnels, conformément à ces conditions.
        </Text>
        <Text style={styles.sub}>Interdictions :</Text>
        <Text style={styles.body}>Vous vous engagez à ne pas :</Text>
        <Text style={styles.bullet}>• Utiliser l'Application pour des activités illégales ou frauduleuses.</Text>
        <Text style={styles.bullet}>• Perturber ou interférer avec le bon fonctionnement de l'Application.</Text>
        <Text style={styles.bullet}>• Reproduire, distribuer ou vendre l'Application sans notre autorisation explicite.</Text>

        <Text style={styles.title}>3. Comptes utilisateur</Text>
        <Text style={styles.sub}>Création de compte :</Text>
        <Text style={styles.body}>
          Pour accéder à certaines fonctionnalités de l'Application, vous devrez créer un compte utilisateur
          en fournissant des informations personnelles véridiques.
        </Text>
        <Text style={styles.sub}>Responsabilité du compte :</Text>
        <Text style={styles.body}>
          Vous êtes responsable de la sécurité de votre compte et de toutes les activités qui se produisent
          sous votre compte.
        </Text>
        <Text style={styles.sub}>Suspension ou résiliation :</Text>
        <Text style={styles.body}>
          Nous nous réservons le droit de suspendre ou de résilier votre compte en cas de violation des
          présentes conditions.
        </Text>

        <Text style={styles.title}>4. Paiements et Transactions</Text>
        <Text style={styles.body}>
          L'Application peut proposer des transactions financières, y compris l'achat de produits ou
          services. Vous acceptez de respecter toutes les politiques de paiement et de transaction
          applicables.
        </Text>

        <Text style={styles.title}>5. Propriété intellectuelle</Text>
        <Text style={styles.body}>
          Tous les droits de propriété intellectuelle relatifs à l'Application, y compris les droits
          d'auteur, marques déposées et autres droits de propriété, sont détenus par Spaceness ou ses
          concédants de licence.
        </Text>

        <Text style={styles.title}>6. Modifications des Conditions</Text>
        <Text style={styles.body}>
          Nous nous réservons le droit de modifier les présentes conditions à tout moment. Les modifications
          entreront en vigueur dès leur publication sur cette page. Vous devez consulter régulièrement cette
          page pour prendre connaissance des éventuelles modifications.
        </Text>

        <Text style={styles.title}>7. Limitation de responsabilité</Text>
        <Text style={styles.body}>
          Dans toute la mesure permise par la loi applicable, nous ne serons pas responsables des dommages
          directs, indirects, accessoires, spéciaux ou punitifs découlant de votre utilisation ou de votre
          incapacité à utiliser l'Application.
        </Text>

        <Text style={styles.title}>8. Loi applicable et juridiction</Text>
        <Text style={styles.body}>
          Les présentes conditions sont régies par la législation de la République démocratique du Congo. En
          cas de litige, les tribunaux de la République démocratique du Congo seront compétents.
        </Text>
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