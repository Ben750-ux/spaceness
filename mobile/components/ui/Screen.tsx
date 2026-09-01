import React from 'react';
import { StyleSheet, Text, View, Pressable, ScrollView, RefreshControlProps } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Colors, Radius } from '@/constants/theme';
import type { IconName } from './Button';

interface ScreenProps {
  children: React.ReactNode;
  scroll?: boolean;
  refreshControl?: React.ReactElement<RefreshControlProps>;
  contentContainerStyle?: object;
  style?: object;
}

export const Screen: React.FC<ScreenProps> = ({ children, scroll = true, refreshControl, contentContainerStyle, style }) => {
  return (
    <SafeAreaView style={[styles.safe, style]} edges={['top', 'left', 'right']}>
      {scroll ? (
        <ScrollView contentContainerStyle={[{ padding: 16, paddingBottom: 32 }, contentContainerStyle]} refreshControl={refreshControl} keyboardShouldPersistTaps="handled">
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.flat, contentContainerStyle]}>{children}</View>
      )}
    </SafeAreaView>
  );
};

export const ScreenWithoutScroll: React.FC<ScreenProps> = ({ children, style }) => (
  <SafeAreaView style={[styles.safe, style]} edges={['top', 'left', 'right']}>
    <View style={styles.flat}>{children}</View>
  </SafeAreaView>
);

interface ScreenHeaderProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  right?: React.ReactNode;
}

export const ScreenHeader: React.FC<ScreenHeaderProps> = ({ title, subtitle, onBack, right }) => {
  const router = useRouter();
  return (
    <View style={styles.header}>
      <Pressable onPress={onBack ?? (() => router.back())} hitSlop={8} style={styles.backBtn}>
        <Ionicons name="chevron-back" size={24} color={Colors.text} />
      </Pressable>
      <View style={styles.headerText}>
        <Text style={styles.headerTitle} numberOfLines={1}>{title}</Text>
        {subtitle ? <Text style={styles.headerSubtitle} numberOfLines={1}>{subtitle}</Text> : null}
      </View>
      <View style={styles.headerRight}>{right}</View>
    </View>
  );
};

interface BadgeProps {
  icon: IconName;
  label: string;
  color?: string;
  bgColor?: string;
}

export const Badge: React.FC<BadgeProps> = ({ icon, label, color = Colors.text, bgColor = Colors.surfaceMuted }) => (
  <View style={[styles.badge, { backgroundColor: bgColor }]}>
    <Ionicons name={icon} size={13} color={color} />
    <Text style={[styles.badgeText, { color }]}>{label}</Text>
  </View>
);

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  flat: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: Radius.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: { flex: 1 },
  headerTitle: { fontSize: 20, fontWeight: '800', color: Colors.text },
  headerSubtitle: { fontSize: 13, color: Colors.textSecondary },
  headerRight: { minWidth: 38, alignItems: 'flex-end' },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: Radius.full,
    gap: 4,
  },
  badgeText: { fontSize: 12, fontWeight: '600' },
});
