import React, { useState } from 'react';
import { StyleSheet, Text, View, KeyboardAvoidingView, Platform, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Radius, Spacing } from '@/constants/theme';
import * as api from '@/lib/api';

const GENDERS = ['homme', 'femme', 'autre'] as const;

export default function SignupScreen() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [gender, setGender] = useState<string>('homme');
  const [email, setEmail] = useState('');
  const [address, setAddress] = useState('');
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [terms, setTerms] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignup = async () => {
    if (!fullName.trim() || !email.trim() || !password) {
      setError('Tous les champs sont obligatoires.');
      return;
    }
    if (!/@/.test(email)) { setError('Email invalide.'); return; }
    if (password.length < 6) { setError('Le mot de passe doit faire au moins 6 caractères.'); return; }
    if (password !== confirm) { setError('Les mots de passe ne correspondent pas.'); return; }
    if (!terms || !privacy) { setError('Vous devez accepter les conditions et la politique de confidentialité.'); return; }

    setError('');
    setLoading(true);
    const res = await api.register(fullName.trim(), email.trim(), password, 'client');
    setLoading(false);
    if (res.ok) {
      // Tente une connexion pour récupérer l'utilisateur → direction vérification
      const loginRes = await api.login(email.trim(), password);
      if (loginRes.verification_required && loginRes.user) {
        router.replace({ pathname: '/verify', params: { userId: String(loginRes.user.id) } });
      } else {
        router.replace('/(auth)/login');
      }
    } else {
      setError(res.message || 'Erreur lors de la création du compte.');
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScreenHeader title="Créer un compte" subtitle="Rejoignez Spaceness" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <View style={styles.content}>
          <TextField label="Nom complet" icon="person-outline" placeholder="Votre nom" value={fullName} onChangeText={setFullName} />

          <Text style={styles.sectionLabel}>Genre</Text>
          <View style={styles.segment}>
            {GENDERS.map((g) => (
              <Pressable key={g} onPress={() => setGender(g)} style={[styles.segmentItem, gender === g && styles.segmentItemActive]}>
                <Text style={[styles.segmentText, gender === g && styles.segmentTextActive]}>{g}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.sectionLabel}>Date de naissance</Text>
          <View style={styles.birthRow}>
            <TextField label={undefined} placeholder="JJ" keyboardType="number-pad" maxLength={2} value={birthDay} onChangeText={setBirthDay} style={styles.birthInput} />
            <TextField label={undefined} placeholder="MM" keyboardType="number-pad" maxLength={2} value={birthMonth} onChangeText={setBirthMonth} style={styles.birthInput} />
            <TextField label={undefined} placeholder="AAAA" keyboardType="number-pad" maxLength={4} value={birthYear} onChangeText={setBirthYear} style={styles.birthYear} />
          </View>
          <Text style={styles.hint}>Format : 15 / 06 / 1998</Text>

          <TextField label="Email" icon="mail-outline" placeholder="vous@email.com" keyboardType="email-address" autoCapitalize="none" value={email} onChangeText={setEmail} />
          <TextField label="Adresse" icon="location-outline" placeholder="Quartier, avenue..." value={address} onChangeText={setAddress} />
          <TextField label="Mot de passe" icon="lock-closed-outline" placeholder="Au moins 6 caractères" secureTextEntry value={password} onChangeText={setPassword} />
          <TextField label="Confirmer le mot de passe" icon="lock-closed-outline" placeholder="••••••••" secureTextEntry value={confirm} onChangeText={setConfirm} />

          <Pressable onPress={() => setTerms(!terms)} style={styles.checkRow}>
            <Ionicons name={terms ? 'checkbox' : 'square-outline'} size={22} color={terms ? Colors.primary : Colors.textLight} />
            <Text style={styles.checkText}>J'accepte les <Text style={styles.link}>conditions d'utilisation</Text></Text>
          </Pressable>
          <Pressable onPress={() => setPrivacy(!privacy)} style={styles.checkRow}>
            <Ionicons name={privacy ? 'checkbox' : 'square-outline'} size={22} color={privacy ? Colors.primary : Colors.textLight} />
            <Text style={styles.checkText}>J'accepte la <Text style={styles.link}>politique de confidentialité</Text></Text>
          </Pressable>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button title="S'inscrire" onPress={handleSignup} loading={loading} icon="person-add-outline" />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flex: { flex: 1 },
  content: { padding: 20, paddingBottom: 32 },
  sectionLabel: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, marginBottom: 8 },
  segment: { flexDirection: 'row', backgroundColor: Colors.surfaceMuted, borderRadius: Radius.md, padding: 4, marginBottom: 16 },
  segmentItem: { flex: 1, paddingVertical: 9, alignItems: 'center', borderRadius: Radius.sm },
  segmentItemActive: { backgroundColor: Colors.surface },
  segmentText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '600', textTransform: 'capitalize' },
  segmentTextActive: { color: Colors.primary, fontWeight: '700' },
  birthRow: { flexDirection: 'row', gap: 8 },
  birthInput: { width: 70 },
  birthYear: { flex: 1 },
  hint: { fontSize: 12, color: Colors.textLight, marginTop: -12, marginBottom: 16 },
  checkRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginVertical: 6 },
  checkText: { flex: 1, fontSize: 14, color: Colors.textSecondary },
  link: { color: Colors.primary, fontWeight: '600' },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
});
