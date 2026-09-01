import React, { useState } from 'react';
import { StyleSheet, Text, TextInput, TextInputProps, View, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Radius } from '@/constants/theme';
import type { IconName } from './Button';

interface TextFieldProps extends TextInputProps {
  label?: string;
  icon?: IconName;
  error?: string;
}

export const TextField: React.FC<TextFieldProps> = ({ label, icon, error, style, multiline, ...props }) => {
  const [focused, setFocused] = useState(false);
  const [hidden, setHidden] = useState(false);
  const isPassword = props.secureTextEntry;

  return (
    <View style={styles.wrapper}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <View style={[styles.container, multiline && styles.containerMultiline, focused && styles.containerFocused, error && styles.containerError]}>
        {icon ? <Ionicons name={icon} size={20} color={focused ? Colors.primary : Colors.textLight} style={styles.leftIcon} /> : null}
        <TextInput
          {...props}
          multiline={multiline}
          secureTextEntry={isPassword ? !hidden : props.secureTextEntry}
          onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); props.onBlur?.(e); }}
          placeholderTextColor={Colors.textLight}
          style={[styles.input, multiline && styles.inputMultiline, style]}
        />
        {isPassword ? (
          <Pressable onPress={() => setHidden(!hidden)} hitSlop={10}>
            <Ionicons name={hidden ? 'eye-off-outline' : 'eye-outline'} size={20} color={Colors.textLight} />
          </Pressable>
        ) : null}
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: { marginBottom: 16 },
  label: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, marginBottom: 8 },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    backgroundColor: Colors.surface,
    paddingHorizontal: 14,
    height: 52,
  },
  containerMultiline: {
    height: undefined,
    alignItems: 'flex-start',
    minHeight: 100,
  },
  containerFocused: { borderColor: Colors.primary, backgroundColor: Colors.surface },
  containerError: { borderColor: Colors.danger },
  input: { flex: 1, fontSize: 16, color: Colors.text, paddingVertical: 0 },
  inputMultiline: { paddingTop: 12, paddingBottom: 12, textAlignVertical: 'top' },
  leftIcon: { marginRight: 10 },
  error: { color: Colors.danger, fontSize: 12, marginTop: 6 },
});
