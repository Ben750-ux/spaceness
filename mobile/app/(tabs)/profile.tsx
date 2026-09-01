import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import type { User } from '@/lib/types';

export default function ProfileScreen() {
  const router = useRouter();
  const { user: contextUser, signOut } = useAuth();
  const [user, setUser] = useState<User | null>(contextUser);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!contextUser?.id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const fresh = await api.getUserById(contextUser.id);
    setUser(fresh ?? contextUser);
    setLoading(false);
  }, [contextUser]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const handleSignOut = async () => {
    await signOut();
    router.replace('/(auth)/login');
  };

  const initial = (user?.full_name || '?').trim().charAt(0).toUpperCase();
  const roleLabel = user?.role === 'client' ? 'Client' : user?.role;

  const infoRows: { icon: keyof typeof Ionicons.glyphMap; label: string; value: string }[] = [
    { icon: 'mail-outline', label: 'Email', value: user?.email || '—' },
    { icon: 'call-outline', label: 'Téléphone', value: user?.phone || '—' },
    { icon: 'location-outline', label: 'Adresse', value: user?.address || '—' },
    { icon: 'time-outline', label: 'Date de naissance', value: user?.birth_date || '—' },
    { icon: 'person-outline', label: 'Genre', value: user?.gender || '—' },
  ];

  const menuItems: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }[] = [
    { icon: 'heart-outline', label: 'Mes favoris', onPress: () => router.push('/favorites') },
    { icon: 'time-outline', label: 'Historique', onPress: () => router.push('/history') },
    { icon: 'chatbubbles-outline', label: "Contacter l'administrateur", onPress: () => router.push('/contact') },
  ];

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <Text style={styles.headerTitle}>Mon profil</Text>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <View style={styles.headerCard}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{initial}</Text>
            </View>
            <Text style={styles.name}>{user?.full_name || 'Utilisateur'}</Text>
            {roleLabel ? (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{roleLabel}</Text>
              </View>
            ) : null}
            {user?.email ? <Text style={styles.email}>{user.email}</Text> : null}
          </View>
        </View>

        <View style={styles.card}>
          {infoRows.map((row, index) => (
            <View key={row.label}>
              {index > 0 ? <View style={styles.separator} /> : null}
              <View style={styles.infoRow}>
                <Ionicons name={row.icon} size={20} color={Colors.primary} />
                <View style={styles.infoTextWrap}>
                  <Text style={styles.infoLabel}>{row.label}</Text>
                  <Text style={styles.infoValue}>{row.value}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={Colors.textLight} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.card}>
          {menuItems.map((item, index) => (
            <View key={item.label}>
              {index > 0 ? <View style={styles.separator} /> : null}
              <Pressable style={styles.menuRow} onPress={item.onPress}>
                <Ionicons name={item.icon} size={20} color={Colors.primary} />
                <Text style={styles.menuLabel}>{item.label}</Text>
                <Ionicons name="chevron-forward" size={18} color={Colors.textLight} />
              </Pressable>
            </View>
          ))}
        </View>

        <Pressable style={styles.logoutBtn} onPress={handleSignOut}>
          <Ionicons name="log-out-outline" size={20} color={Colors.danger} />
          <Text style={styles.logoutText}>Se déconnecter</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  headerTitle: { fontSize: 24, fontWeight: '800', color: Colors.text, paddingHorizontal: 16, paddingVertical: 14 },
  content: { padding: 16 },
  card: { backgroundColor: Colors.surface, borderRadius: Radius.lg, padding: 16, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2, marginBottom: 16 },
  headerCard: { alignItems: 'center', paddingVertical: 8 },
  avatar: { width: 84, height: 84, borderRadius: 42, backgroundColor: Colors.primary, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  avatarText: { color: '#fff', fontSize: 34, fontWeight: '800' },
  name: { fontSize: 20, fontWeight: '800', color: Colors.text, textAlign: 'center' },
  badge: { backgroundColor: Colors.primaryLight, borderRadius: Radius.full, paddingHorizontal: 12, paddingVertical: 3, marginTop: 8, alignSelf: 'center' },
  badgeText: { color: Colors.primary, fontSize: 12, fontWeight: '700', textTransform: 'capitalize' },
  email: { color: Colors.textSecondary, fontSize: 14, marginTop: 8, textAlign: 'center' },
  separator: { height: 1, backgroundColor: Colors.border },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12 },
  infoTextWrap: { flex: 1 },
  infoLabel: { fontSize: 13, color: Colors.textSecondary },
  infoValue: { fontSize: 15, color: Colors.text, fontWeight: '600', marginTop: 2 },
  menuRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 14 },
  menuLabel: { flex: 1, fontSize: 15, fontWeight: '600', color: Colors.text },
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: Colors.surface, borderRadius: Radius.lg, paddingVertical: 15, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, shadowOffset: { width: 0, height: 2 }, elevation: 2 },
  logoutText: { color: Colors.danger, fontSize: 15, fontWeight: '700' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
});
