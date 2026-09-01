import React, { useState } from 'react';
import { StyleSheet, Text, View, KeyboardAvoidingView, Platform } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors } from '@/constants/theme';
import * as api from '@/lib/api';

export default function ResetScreen() {
  const params = useLocalSearchParams<{ email?: string; code?: string }>();
  const router = useRouter();
  const [code, setCode] = useState(params.code || '');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleReset = async () => {
    if (!/^\d{6}$/.test(code)) { setError('Entrez le code à 6 chiffres.'); return; }
    if (password.length < 6) { setError('Le mot de passe doit faire au moins 6 caractères.'); return; }
    if (password !== confirm) { setError('Les mots de passe ne correspondent pas.'); return; }
    if (!params.email) { setError('Session expirée. Recommencez.'); return; }

    setError('');
    setLoading(true);
    const res = await api.resetPassword(params.email, code, password);
    setLoading(false);
    if (res.ok) {
      setSuccess(true);
      setTimeout(() => router.replace('/(auth)/login'), 1500);
    } else {
      setError(res.message || 'Erreur lors de la réinitialisation.');
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScreenHeader title="Nouveau mot de passe" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <View style={styles.content}>
          {success ? (
            <View style={styles.successBox}>
              <Ionicons name="checkmark-circle" size={56} color={Colors.secondary} />
              <Text style={styles.successTitle}>Mot de passe réinitialisé !</Text>
              <Text style={styles.successSub}>Redirection vers la connexion...</Text>
            </View>
          ) : (
            <>
              <TextField label="Code de réinitialisation" icon="keypad-outline" placeholder="••••••" keyboardType="number-pad" maxLength={6} value={code} onChangeText={setCode} />
              <TextField label="Nouveau mot de passe" icon="lock-closed-outline" placeholder="Au moins 6 caractères" secureTextEntry value={password} onChangeText={setPassword} />
              <TextField label="Confirmer" icon="lock-closed-outline" placeholder="••••••••" secureTextEntry value={confirm} onChangeText={setConfirm} />

              {error ? <Text style={styles.error}>{error}</Text> : null}

              <Button title="Réinitialiser" onPress={handleReset} loading={loading} icon="refresh-outline" />
            </>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flex: { flex: 1 },
  content: { padding: 24 },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
  successBox: { alignItems: 'center', marginTop: 60 },
  successTitle: { fontSize: 22, fontWeight: '800', color: Colors.text, marginTop: 16 },
  successSub: { fontSize: 14, color: Colors.textSecondary, marginTop: 8 },
});
