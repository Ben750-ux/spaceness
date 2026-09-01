import React, { useState } from 'react';
import { StyleSheet, Text, View, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors } from '@/constants/theme';
import * as api from '@/lib/api';

export default function ForgotScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSend = async () => {
    if (!/@/.test(email)) { setError('Entrez une adresse email valide.'); return; }
    setError('');
    setLoading(true);
    const res = await api.forgotPassword(email.trim());
    setLoading(false);
    if (res.ok) {
      router.push({ pathname: '/reset', params: { email: email.trim(), code: res.code || '' } });
    } else {
      setError(res.message || 'Erreur. Vérifiez votre email.');
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScreenHeader title="Mot de passe oublié" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <View style={styles.content}>
          <View style={styles.iconWrap}>
            <Ionicons name="key-outline" size={44} color={Colors.primary} />
          </View>
          <Text style={styles.title}>Réinitialiser le mot de passe</Text>
          <Text style={styles.subtitle}>Entrez votre email pour recevoir un code de réinitialisation.</Text>

          <TextField label="Email" icon="mail-outline" placeholder="vous@email.com" keyboardType="email-address" autoCapitalize="none" value={email} onChangeText={setEmail} />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button title="Envoyer le code" onPress={handleSend} loading={loading} icon="send-outline" />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flex: { flex: 1 },
  content: { padding: 24 },
  iconWrap: { width: 88, height: 88, borderRadius: 44, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginBottom: 18 },
  title: { fontSize: 22, fontWeight: '800', color: Colors.text, textAlign: 'center' },
  subtitle: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', marginTop: 8, marginBottom: 24 },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
});
