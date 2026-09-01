import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Radius } from '@/constants/theme';

export type IconName = keyof typeof Ionicons.glyphMap;

interface ButtonProps {
  title: string;
  onPress?: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  fullWidth?: boolean;
  icon?: IconName;
  iconColor?: string;
  size?: 'sm' | 'md' | 'lg';
  style?: object;
}

const HEIGHTS = { sm: 40, md: 50, lg: 54 };
const FONTS = { sm: 14, md: 16, lg: 17 };

export const Button: React.FC<ButtonProps> = ({ title, onPress, loading, disabled, variant = 'primary', fullWidth = true, icon, iconColor, size = 'md', style }) => {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        { height: HEIGHTS[size] },
        fullWidth && styles.fullWidth,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'outline' || variant === 'ghost' ? Colors.primary : '#fff'} />
      ) : (
        <>
          {icon ? <Ionicons name={icon} size={size === 'sm' ? 16 : FONTS[size]} color={iconColor ?? (variant === 'outline' || variant === 'ghost' ? Colors.primary : '#fff')} style={{ marginRight: 8 }} /> : null}
          <Text style={[styles.text, { fontSize: FONTS[size] }, (variant === 'outline' || variant === 'ghost') && styles.textOutline]}>{title}</Text>
        </>
      )}
    </Pressable>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 20,
  },
  fullWidth: { width: '100%' },
  primary: { backgroundColor: Colors.primary },
  secondary: { backgroundColor: Colors.secondary },
  danger: { backgroundColor: Colors.danger },
  outline: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: Colors.primary },
  ghost: { backgroundColor: 'transparent' },
  disabled: { opacity: 0.5 },
  pressed: { opacity: 0.85, transform: [{ scale: 0.98 }] },
  text: { color: '#fff', fontWeight: '700' },
  textOutline: { color: Colors.primary },
});
