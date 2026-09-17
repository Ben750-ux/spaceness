import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';
import { Colors, Radius } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import type { User } from '@/lib/types';

const GENDERS = ['homme', 'femme', 'autre'] as const;

export default function ProfileEditScreen() {
  const router = useRouter();
  const { user: contextUser } = useAuth();
  const [user, setUser] = useState<User | null>(contextUser);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [gender, setGender] = useState<string>('homme');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!contextUser?.id) { setLoading(false); return; }
    api.getUserById(contextUser.id).then((fresh) => {
      if (fresh) setUser(fresh);
      setLoading(false);
    });
  }, [contextUser]);

  useEffect(() => {
    if (!user) return;
    setFullName(user.full_name || '');
    setPhone(user.phone || '');
    setAddress(user.address || '');
    if (user.gender) setGender(user.gender);
    const parts = (user.birth_date || '').split('/');
    if (parts.length === 3) {
      setBirthDay(parts[0]);
      setBirthMonth(parts[1]);
      setBirthYear(parts[2]);
    }
  }, [user]);

  const handleSave = async () => {
    if (!contextUser?.id) return;
    if (!fullName.trim()) { setError('Le nom est obligatoire.'); return; }
    setError('');
    setSuccess('');
    setSaving(true);
    const birthDate = birthDay && birthMonth && birthYear
      ? `${birthDay.padStart(2, '0')}/${birthMonth.padStart(2, '0')}/${birthYear}`
      : '';
    const res = await api.updateProfile(contextUser.id, {
      full_name: fullName.trim(),
      phone: phone.trim(),
      address: address.trim(),
      birth_date: birthDate,
      gender,
    });
    setSaving(false);
    if (res.ok) {
      setSuccess(res.message || 'Profil mis à jour.');
      setTimeout(() => router.back(), 900);
    } else {
      setError(res.message || 'Erreur lors de la mise à jour.');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <ScreenHeader title="Modifier le profil" subtitle="Spaceness" />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScreenHeader title="Modifier le profil" subtitle="Spaceness" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <TextField label="Nom complet" icon="person-outline" placeholder="Votre nom" value={fullName} onChangeText={setFullName} />
          <TextField label="Téléphone" icon="call-outline" placeholder="+243 ..." keyboardType="phone-pad" value={phone} onChangeText={setPhone} />
          <TextField label="Adresse" icon="location-outline" placeholder="Quartier, avenue..." value={address} onChangeText={setAddress} />

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

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {success ? <Text style={styles.success}>{success}</Text> : null}

          <Button title="Enregistrer" onPress={handleSave} loading={saving} icon="checkmark-outline" />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flex: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  content: { padding: 20, paddingBottom: 40 },
  sectionLabel: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, marginBottom: 8, marginTop: 4 },
  segment: { flexDirection: 'row', backgroundColor: Colors.surfaceMuted, borderRadius: Radius.md, padding: 4, marginBottom: 16 },
  segmentItem: { flex: 1, paddingVertical: 9, alignItems: 'center', borderRadius: Radius.sm },
  segmentItemActive: { backgroundColor: Colors.surface },
  segmentText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '600', textTransform: 'capitalize' },
  segmentTextActive: { color: Colors.primary, fontWeight: '700' },
  birthRow: { flexDirection: 'row', gap: 8 },
  birthInput: { width: 70 },
  birthYear: { flex: 1 },
  hint: { fontSize: 12, color: Colors.textLight, marginTop: -12, marginBottom: 16 },
  error: { color: Colors.danger, fontSize: 13, marginBottom: 12, textAlign: 'center' },
  success: { color: Colors.secondary, fontSize: 13, marginBottom: 12, textAlign: 'center' },
});