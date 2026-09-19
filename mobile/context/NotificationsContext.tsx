import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { Colors, Radius } from '@/constants/theme';
import * as api from '@/lib/api';

const POLL_INTERVAL = 15000;

type NotificationsContextValue = {
  unread: number;
  markAllRead: () => Promise<void>;
};

const NotificationsContext = createContext<NotificationsContextValue>({ unread: 0, markAllRead: async () => {} });

export function useNotifications() {
  return useContext(NotificationsContext);
}

export function NotificationsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const [unread, setUnread] = useState(0);
  const [banner, setBanner] = useState(false);
  const lastShown = useRef(-1);

  useEffect(() => {
    if (!user?.id) {
      setUnread(0);
      lastShown.current = -1;
      return;
    }
    let alive = true;
    lastShown.current = -1;

    const tick = async () => {
      const count = await api.getUnreadMessageCount(user.id);
      if (!alive) return;
      if (lastShown.current === -1) {
        lastShown.current = count;
        setUnread(count);
        return;
      }
      if (count > lastShown.current) {
        lastShown.current = count;
        setUnread(count);
        setBanner(true);
      } else {
        lastShown.current = count;
        setUnread(count);
      }
    };

    tick();
    const interval = setInterval(tick, POLL_INTERVAL);
    return () => {
      alive = false;
      clearInterval(interval);
    };
  }, [user?.id]);

  useEffect(() => {
    if (!banner) return;
    const timer = setTimeout(() => setBanner(false), 5000);
    return () => clearTimeout(timer);
  }, [banner]);

  const markAllRead = useCallback(async () => {
    if (!user?.id) return;
    await api.markMessagesRead(user.id);
    setUnread(0);
    lastShown.current = 0;
    setBanner(false);
  }, [user?.id]);

  const openContact = () => {
    router.push('/contact');
  };

  const value = useMemo(() => ({ unread, markAllRead }), [unread]);

  return (
    <NotificationsContext.Provider value={value}>
      <View style={{ flex: 1 }}>
        {children}
        {banner ? (
          <Pressable style={styles.banner} onPress={openContact}>
            <Ionicons name="chatbubble-ellipses" size={22} color={Colors.primary} />
            <View style={{ flex: 1 }}>
              <Text style={styles.bannerTitle}>Nouveau message</Text>
              <Text style={styles.bannerBody}>Vous avez reçu une réponse de l'administrateur.</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={Colors.textLight} />
          </Pressable>
        ) : null}
      </View>
    </NotificationsContext.Provider>
  );
}

const styles = StyleSheet.create({
  banner: {
    position: 'absolute',
    top: 8,
    left: 12,
    right: 12,
    zIndex: 100,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: 14,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 3 },
    elevation: 5,
    borderWidth: 1,
    borderColor: Colors.primary,
  },
  bannerTitle: { fontSize: 14, fontWeight: '800', color: Colors.text },
  bannerBody: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
});