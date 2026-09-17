import { StyleSheet, Text, View, ScrollView } from 'react-native';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Spacing } from '@/constants/theme';

export default function PrivacyScreen() {
  return (
    <View style={styles.safe}>
      <ScreenHeader title="Politique de confidentialité" subtitle="Spaceness" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>1. Données collectées</Text>
        <Text style={styles.body}>
          Nous collectons les informations fournies lors de la création du compte : nom, genre, date de
          naissance, adresse, email et mot de passe (chiffré).
        </Text>

        <Text style={styles.title}>2. Utilisation des données</Text>
        <Text style={styles.body}>
          Ces données servent à gérer votre compte, traiter vos commandes, assurer la livraison et
          améliorer nos services. Elles ne sont jamais vendues à des tiers.
        </Text>

        <Text style={styles.title}>3. Partage</Text>
        <Text style={styles.body}>
          Les informations nécessaires (nom, adresse, contact) sont transmises aux marchands uniquement
          pour l'exécution de vos commandes.
        </Text>

        <Text style={styles.title}>4. Sécurité</Text>
        <Text style={styles.body}>
          Les mots de passe sont stockés de manière chiffrée et les accès sont protégés. Nous appliquons
          des mesures raisonnables pour protéger vos données.
        </Text>

        <Text style={styles.title}>5. Vos droits</Text>
        <Text style={styles.body}>
          Vous pouvez demander la consultation, la correction ou la suppression de vos données personnelles
          à tout moment via la page contact de l'application.
        </Text>

        <Text style={styles.title}>6. Contact</Text>
        <Text style={styles.body}>
          Pour toute question relative à la confidentialité, contactez-nous via la rubrique support de
          l'application.
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