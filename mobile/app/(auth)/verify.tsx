import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';
import { useAuth } from '@/context/AuthContext';
import { Colors } from '@/constants/theme';
import * as api from '@/lib/api';

export default function VerifyScreen() {
  const params = useLocalSearchParams<{ userId?: string }>();
  const router = useRouter();
  const { signIn, user } = useAuth();
  const userId = Number(params.userId) || user?.id;

  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const canResend = useRef(true);

  useEffect(() => {
    fetchCode();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchCode = async () => {
    if (!userId) return;
    setMessage('');
    setError('');
    const sent = await api.resendVerificationCode(userId);
    if (sent) {
      setMessage('Un code a été envoyé à votre adresse email.');
    } else {
      setError('Envoi impossible. Réessayez plus tard.');
    }
  };

  const handleVerify = async () => {
    if (!userId) { setError('Session expirée. Reconnectez-vous.'); return; }
    if (!/^\d{6}$/.test(code)) { setError('Entrez un code à 6 chiffres.'); return; }
    setError('');
    setLoading(true);
    const res = await api.verifyEmailCode(userId, code);
    setLoading(false);
    if (res.ok && res.user) {
      await signIn({ ...res.user, is_verified: true });
      router.replace('/(tabs)');
    } else {
      setError(res.message || 'Code incorrect.');
    }
  };

  const handleResend = async () => {
    if (!canResend.current) return;
    await fetchCode();
    canResend.current = false;
    setTimeout(() => (canResend.current = true), 30000);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScreenHeader title="Vérification" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.iconWrap}>
            <Ionicons name="shield-checkmark-outline" size={44} color={Colors.primary} />
          </View>
          <Text style={styles.title}>Vérifiez votre email</Text>
          <Text style={styles.subtitle}>Saisissez le code à 6 chiffres envoyé par email.</Text>

          <TextField
            label="Code"
            icon="keypad-outline"
            placeholder="••••••"
            keyboardType="number-pad"
            maxLength={6}
            value={code}
            onChangeText={setCode}
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {message ? <Text style={styles.success}>{message}</Text> : null}

          <Button title="Vérifier" onPress={handleVerify} loading={loading} icon="checkmark-circle-outline" />

          <Button title="Renvoyer le code" variant="ghost" onPress={handleResend} icon="refresh-outline" />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flex: { flex: 1 },
  content: { padding: 24, paddingTop: 12 },
  iconWrap: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: Colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 18,
  },
  title: { fontSize: 22, fontWeight: '800', color: Colors.text, textAlign: 'center' },
  subtitle: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', marginTop: 8, marginBottom: 24 },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
  success: { color: Colors.secondary, fontSize: 13, marginBottom: 12, textAlign: 'center' },
});
