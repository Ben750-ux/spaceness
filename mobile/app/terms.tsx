import { StyleSheet, Text, View, ScrollView } from 'react-native';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Spacing } from '@/constants/theme';

export default function TermsScreen() {
  return (
    <View style={styles.safe}>
      <ScreenHeader title="Conditions d'utilisation" subtitle="Spaceness" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>1. Objet</Text>
        <Text style={styles.body}>
          Les présentes conditions régissent l'utilisation de la plateforme Spaceness, marché en ligne
          de Lubumbashi. En créant un compte, vous acceptez l'ensemble de ces conditions.
        </Text>

        <Text style={styles.title}>2. Compte utilisateur</Text>
        <Text style={styles.body}>
          Vous êtes responsable de la confidentialité de vos identifiants et de l'ensemble des actions
          effectuées via votre compte. Toute information inexacte peut entraîner la suspension du compte.
        </Text>

        <Text style={styles.title}>3. Commandes et paiements</Text>
        <Text style={styles.body}>
          Les commandes sont validées lors de l'enregistrement du paiement. Le marchand confirme la
          disponibilité des articles avant expédition. En cas d'indisponibilité, le remboursement est
          effectué selon les modalités convenues avec le marchand.
        </Text>

        <Text style={styles.title}>4. Livraison</Text>
        <Text style={styles.body}>
          Les délais de livraison sont communiqués lors du passage de la commande. Le client doit vérifier
          sa commande à la réception et signaler toute anomalie sous 48 heures.
        </Text>

        <Text style={styles.title}>5. Responsabilités</Text>
        <Text style={styles.body}>
          Spaceness agit en tant que plateforme de mise en relation. La qualité des produits et du service
          après-vente relève de la responsabilité des marchands.
        </Text>

        <Text style={styles.title}>6. Modifications</Text>
        <Text style={styles.body}>
          Nous pouvons modifier ces conditions à tout moment. Les nouvelles conditions sont applicables
          dès leur publication dans l'application.
        </Text>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.lg, paddingBottom: 48 },
  title: { fontSize: 17, fontWeight: '700', color: Colors.text, marginTop: 20, marginBottom: 6 },
  body: { fontSize: 14, lineHeight: 22, color: Colors.textSecondary },
});