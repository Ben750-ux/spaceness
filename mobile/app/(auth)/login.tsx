import React, { useState } from 'react';
import { StyleSheet, Text, View, KeyboardAvoidingView, Platform, Pressable } from 'react-native';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/context/AuthContext';
import { Colors, Radius, Spacing } from '@/constants/theme';
import * as api from '@/lib/api';
import { Link } from 'expo-router';

export default function LoginScreen() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setError('Veuillez remplir tous les champs.');
      return;
    }
    setError('');
    setLoading(true);
    const res = await api.login(email.trim(), password);
    setLoading(false);

    if (res.verification_required && res.user) {
      // Compte non vérifié : envoie un nouveau code et redirige
      setError('');
      router.push({
        pathname: '/verify',
        params: { userId: String(res.user.id) },
      });
      return;
    }
    if (res.ok && res.user) {
      if (res.user.role !== 'client') {
        setError('Cette application est réservée aux comptes clients.');
        return;
      }
      await signIn({ ...res.user, is_verified: true });
      router.replace('/(tabs)');
    } else {
      setError(res.message || 'Email ou mot de passe incorrect.');
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex} keyboardVerticalOffset={50}>
        <View style={styles.hero}>
          <View style={styles.logoWrap}>
            <Ionicons name="bag-handle" size={36} color="#fff" />
          </View>
          <Text style={styles.appName}>Spaceness</Text>
          <Text style={styles.tagline}>Le marché en ligne de Lubumbashi</Text>
        </View>

        <View style={styles.formCard}>
          <Text style={styles.welcome}>Bon retour 👋</Text>
          <Text style={styles.welcomeSub}>Connectez-vous pour continuer</Text>

          <TextField
            label="Email"
            icon="mail-outline"
            placeholder="vous@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
            value={email}
            onChangeText={setEmail}
          />
          <TextField
            label="Mot de passe"
            icon="lock-closed-outline"
            placeholder="••••••••"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            onSubmitEditing={handleLogin}
          />

          <View style={styles.forgotRow}>
            <Link href="/forgot" asChild>
              <Pressable>
                <Text style={styles.forgotLink}>Mot de passe oublié ?</Text>
              </Pressable>
            </Link>
          </View>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Button title="Se connecter" onPress={handleLogin} loading={loading} icon="log-in-outline" />

          <View style={styles.dividerRow}>
            <View style={styles.divider} />
            <Text style={styles.dividerText}>ou</Text>
            <View style={styles.divider} />
          </View>

          <Link href="/signup" asChild>
            <Pressable>
              <Button title="Créer un compte" variant="outline" icon="person-add-outline" />
            </Pressable>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.primary },
  flex: { flex: 1 },
  hero: { alignItems: 'center', paddingTop: 48, paddingBottom: 40 },
  logoWrap: {
    width: 76,
    height: 76,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  appName: { fontSize: 30, fontWeight: '900', color: '#fff', letterSpacing: 0.5 },
  tagline: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginTop: 6 },
  formCard: {
    flex: 1,
    backgroundColor: Colors.background,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    paddingHorizontal: 24,
    paddingTop: 28,
  },
  welcome: { fontSize: 24, fontWeight: '800', color: Colors.text },
  welcomeSub: { fontSize: 14, color: Colors.textSecondary, marginBottom: 24, marginTop: 4 },
  forgotRow: { alignItems: 'flex-end', marginBottom: 8 },
  forgotLink: { color: Colors.primary, fontSize: 14, fontWeight: '600' },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
  dividerRow: { flexDirection: 'row', alignItems: 'center', marginVertical: Spacing.lg },
  divider: { flex: 1, height: 1, backgroundColor: Colors.border },
  dividerText: { marginHorizontal: 12, color: Colors.textLight, fontSize: 13 },
});
