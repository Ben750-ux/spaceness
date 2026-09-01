import React, { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import type { Message } from '@/lib/types';
import { TextField } from '@/components/ui/TextField';
import { Button } from '@/components/ui/Button';
import { ScreenHeader } from '@/components/ui/Screen';

export default function ContactScreen() {
  const { user } = useAuth();
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const load = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    const data = await api.getUserMessages(user.id);
    setMessages(data);
    setLoading(false);
  }, [user?.id]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const handleSend = async () => {
    if (!user?.id || !subject.trim() || !message.trim()) return;
    setSending(true);
    const ok = await api.sendAdminMessage(user.id, subject.trim(), message.trim());
    setSending(false);
    if (ok) {
      setSubject('');
      setMessage('');
      load();
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <ScreenHeader title="Contacter l'admin" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <TextField label="Sujet" value={subject} onChangeText={setSubject} placeholder="Sujet de votre message" />
          <TextField
            label="Message"
            value={message}
            onChangeText={setMessage}
            placeholder="Décrivez votre demande..."
            multiline
            style={{ minHeight: 100, textAlignVertical: 'top' }}
          />
          <Button title="Envoyer" onPress={handleSend} loading={sending} disabled={!subject.trim() || !message.trim()} />
        </View>

        <Text style={styles.sectionTitle}>Vos messages</Text>

        {loading ? (
          <ActivityIndicator size="large" color={Colors.primary} style={{ marginTop: 32 }} />
        ) : messages.length === 0 ? (
          <Text style={styles.emptyText}>Aucun message pour le moment.</Text>
        ) : (
          messages.map((msg) => (
            <View key={msg.id} style={styles.card}>
              <Text style={styles.msgHeader}>
                {msg.created_at ? msg.created_at.substr(0, 10) : ''} — {msg.subject}
              </Text>
              <Text style={styles.msgBody}>{msg.message}</Text>
              {msg.admin_reply ? (
                <View style={styles.replyBox}>
                  <Text style={styles.replyLabel}>Réponse :</Text>
                  <Text style={styles.replyText}>{msg.admin_reply}</Text>
                </View>
              ) : null}
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.lg, paddingBottom: 32 },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: Colors.text, marginBottom: 12 },
  emptyText: { color: Colors.textSecondary, fontSize: 14, textAlign: 'center', marginTop: 16 },
  msgHeader: { fontSize: 14, fontWeight: '700', color: Colors.text, marginBottom: 6 },
  msgBody: { fontSize: 14, color: Colors.textSecondary, lineHeight: 20 },
  replyBox: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  replyLabel: { fontSize: 13, fontWeight: '700', color: Colors.secondary, marginBottom: 4 },
  replyText: { fontSize: 14, color: Colors.secondary, lineHeight: 20 },
});
