import { useCallback, useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { NotificationsProvider } from '@/context/NotificationsContext';
import * as api from '@/lib/api';

function BlockedScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.blockedWrap}>
      <View style={styles.blockedGlow} />
      <View style={styles.blockedLogo}>
        <Text style={styles.blockedLogoText}>S</Text>
      </View>
      <View style={styles.blockedCard}>
        <View style={styles.blockedLock}>
          <Text style={styles.blockedIcon}>🔒</Text>
        </View>
        <Text style={styles.blockedTitle}>Application bloquée</Text>
        <Text style={styles.blockedMsg}>
          {message || "L'application est temporairement bloquée par l'administration. Revenez plus tard."}
        </Text>
        <Pressable
          style={({ pressed }) => [styles.blockedBtn, pressed && styles.blockedBtnPressed]}
          onPress={onRetry}
        >
          <Text style={styles.blockedBtnText}>Réessayer</Text>
        </Pressable>
      </View>
      <Text style={styles.blockedFoot}>Spaceness — {String(new Date().getFullYear())}</Text>
    </View>
  );
}

function BlockedGate() {
  const [state, setState] = useState<'checking' | 'ok' | 'blocked'>('checking');
  const [blockMsg, setBlockMsg] = useState('');

  const check = useCallback(async () => {
    const s = await api.getAppSettings();
    setState(s.is_blocked ? 'blocked' : 'ok');
    setBlockMsg(s.block_message || '');
  }, []);

  useEffect(() => {
    check();
    const iv = setInterval(check, 20000);
    const sub = AppState.addEventListener('change', (next) => { if (next === 'active') check(); });
    return () => { clearInterval(iv); sub.remove(); };
  }, [check]);

  if (state === 'blocked') return <BlockedScreen message={blockMsg} onRetry={check} />;

  if (state === 'checking') {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' }}>
        <ActivityIndicator size="large" color="#009fe3" />
      </View>
    );
  }

  return <RootNavigator />;
}

function RootNavigator() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff' }}>
        <ActivityIndicator size="large" color="#009fe3" />
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="product/[id]" />
        <Stack.Screen name="shop/[id]" />
        <Stack.Screen name="checkout" />
        <Stack.Screen name="favorites" />
        <Stack.Screen name="history" />
        <Stack.Screen name="contact" />
        <Stack.Screen name="terms" />
        <Stack.Screen name="privacy" />
        <Stack.Screen name="profile-edit" />
      </Stack>
    </View>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <NotificationsProvider>
        <BlockedGate />
      </NotificationsProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  blockedWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0b1220', padding: 24 },
  blockedGlow: { position: 'absolute', top: -80, right: -60, width: 260, height: 260, borderRadius: 130, backgroundColor: 'rgba(0, 159, 227, 0.18)' },
  blockedLogo: { width: 72, height: 72, borderRadius: 22, backgroundColor: '#009fe3', alignItems: 'center', justifyContent: 'center', shadowColor: '#009fe3', shadowOpacity: 0.55, shadowRadius: 18, shadowOffset: { width: 0, height: 6 }, elevation: 12, marginBottom: 22 },
  blockedLogoText: { color: '#fff', fontSize: 36, fontWeight: '900' },
  blockedCard: { width: '100%', maxWidth: 340, backgroundColor: '#fff', borderRadius: 20, padding: 28, alignItems: 'center', shadowColor: '#000', shadowOpacity: 0.3, shadowRadius: 24, shadowOffset: { width: 0, height: 12 }, elevation: 14 },
  blockedLock: { width: 60, height: 60, borderRadius: 30, backgroundColor: '#fef2f2', alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  blockedIcon: { fontSize: 26 },
  blockedTitle: { fontSize: 21, fontWeight: '800', color: '#0f172a', textAlign: 'center' },
  blockedMsg: { fontSize: 14.5, color: '#475569', marginTop: 10, textAlign: 'center', lineHeight: 22 },
  blockedBtn: { marginTop: 22, backgroundColor: '#009fe3', paddingVertical: 13, paddingHorizontal: 40, borderRadius: 12, alignSelf: 'stretch', alignItems: 'center' },
  blockedBtnPressed: { opacity: 0.8, transform: [{ scale: 0.98 }] },
  blockedBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  blockedFoot: { marginTop: 24, color: 'rgba(255,255,255,0.4)', fontSize: 12 },
});
