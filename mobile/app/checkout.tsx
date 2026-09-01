import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/TextField';
import { Colors, Radius, Spacing } from '@/constants/theme';

export default function CheckoutScreen() {
  const router = useRouter();
  const { user, cart, clearCart } = useAuth();
  const mountedRef = useRef(true);

  const [quartier, setQuartier] = useState('');
  const [detail, setDetail] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  const total = useMemo(() => cart.reduce((sum, i) => sum + i.price * i.qty, 0), [cart]);
  const formattedTotal = useMemo(() => total.toLocaleString('fr-FR') + ' FC', [total]);

  const itemsPayload = useMemo(
    () => cart.map((i) => ({ product_id: i.product_id, qty: i.qty })),
    [cart],
  );

  const handleConfirm = useCallback(async () => {
    if (!user) return;
    setError('');

    if (!quartier.trim()) {
      setError('Le quartier est requis.');
      return;
    }
    if (phone.trim().length < 9) {
      setError('Le numéro de téléphone doit contenir au moins 9 chiffres.');
      return;
    }

    const deliveryAddress = detail.trim()
      ? `${quartier.trim()} - ${detail.trim()}, Lubumbashi`
      : `${quartier.trim()}, Lubumbashi`;

    setLoading(true);
    try {
      const res = await api.createOrdersFromCart(user.id, itemsPayload, deliveryAddress, phone.trim());
      if (!mountedRef.current) return;

      if (res.ok) {
        setSuccess(true);
        clearCart();
        setTimeout(() => {
          if (mountedRef.current) router.replace('/(tabs)/orders');
        }, 1500);
      } else {
        setError(res.message || 'Erreur lors de la commande.');
      }
    } catch {
      if (mountedRef.current) setError('Erreur réseau. Veuillez réessayer.');
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [user, quartier, detail, phone, itemsPayload, clearCart, router]);

  if (success) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.successWrap}>
          <Ionicons name="checkmark-circle" size={72} color={Colors.secondary} />
          <Text style={styles.successTitle}>Commande confirmée!</Text>
          <Text style={styles.successSub}>Redirection vers vos commandes...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (cart.length === 0) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Paiement & livraison</Text>
        </View>
        <View style={styles.emptyWrap}>
          <Ionicons name="cart-outline" size={64} color={Colors.textLight} />
          <Text style={styles.emptyTitle}>Votre panier est vide</Text>
          <Text style={styles.emptySub}>Ajoutez des articles avant de passer commande.</Text>
          <View style={styles.emptyCta}>
            <Button title="Retour au marché" onPress={() => router.replace('/(tabs)')} icon="storefront-outline" variant="outline" />
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Paiement & livraison</Text>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="bag-check-outline" size={20} color={Colors.primary} />
            <Text style={styles.cardTitle}>Récapitulatif</Text>
          </View>

          {cart.map((item, idx) => (
            <View key={String(item.product_id)}>
              {idx > 0 && <View style={styles.divider} />}
              <View style={styles.itemRow}>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName} numberOfLines={1}>{item.name}</Text>
                  <Text style={styles.itemQty}>{item.qty} x {item.price.toLocaleString('fr-FR')} FC</Text>
                </View>
                <Text style={styles.itemSubtotal}>
                  {(item.price * item.qty).toLocaleString('fr-FR')} FC
                </Text>
              </View>
            </View>
          ))}

          <View style={styles.totalDivider} />
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalValue}>{formattedTotal}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="location-outline" size={20} color={Colors.primary} />
            <Text style={styles.cardTitle}>Adresse de livraison</Text>
          </View>

          <TextField
            label="Quartier"
            icon="location-outline"
            placeholder="Ex: Kasuku, Katuba..."
            value={quartier}
            onChangeText={setQuartier}
            autoCapitalize="words"
          />

          <TextField
            label="Adresse détail (optionnel)"
            placeholder="Numéro, repère..."
            value={detail}
            onChangeText={setDetail}
            autoCapitalize="sentences"
          />
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="call-outline" size={20} color={Colors.primary} />
            <Text style={styles.cardTitle}>Téléphone</Text>
          </View>

          <TextField
            label="Numéro de téléphone"
            icon="call-outline"
            placeholder="09XXXXXXXX"
            value={phone}
            onChangeText={(t) => setPhone(t.replace(/[^0-9]/g, ''))}
            keyboardType="phone-pad"
            maxLength={15}
          />
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Ionicons name="alert-circle" size={18} color={Colors.danger} />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <View style={styles.footerTotal}>
          <Text style={styles.footerTotalLabel}>Total</Text>
          <Text style={styles.footerTotalValue}>{formattedTotal}</Text>
        </View>
        <Button
          title="Confirmer la commande"
          onPress={handleConfirm}
          loading={loading}
          icon="bag-check-outline"
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: Colors.text },
  scroll: { flex: 1 },
  scrollContent: { padding: 16, paddingBottom: 24 },

  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: 16,
    marginBottom: 16,
    shadowColor: Colors.text,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  cardTitle: { fontSize: 16, fontWeight: '700', color: Colors.text },

  itemRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  itemInfo: { flex: 1, marginRight: 12 },
  itemName: { fontSize: 14, fontWeight: '600', color: Colors.text },
  itemQty: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  itemSubtotal: { fontSize: 14, fontWeight: '700', color: Colors.text },

  divider: { height: 1, backgroundColor: Colors.border, marginVertical: 10 },
  totalDivider: { height: 1, backgroundColor: Colors.border, marginVertical: 12 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  totalLabel: { fontSize: 16, fontWeight: '600', color: Colors.textSecondary },
  totalValue: { fontSize: 20, fontWeight: '800', color: Colors.primary },

  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#fef2f2',
    borderRadius: Radius.md,
    padding: 12,
    marginBottom: 16,
  },
  errorText: { flex: 1, fontSize: 13, color: Colors.danger, fontWeight: '500' },

  footer: {
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.surface,
    padding: 16,
    paddingBottom: 20,
  },
  footerTotal: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  footerTotalLabel: { fontSize: 14, color: Colors.textSecondary },
  footerTotalValue: { fontSize: 18, fontWeight: '800', color: Colors.text },

  emptyWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: Colors.text, marginTop: 16 },
  emptySub: { fontSize: 14, color: Colors.textSecondary, marginTop: 6, textAlign: 'center' },
  emptyCta: { marginTop: 24, width: '100%' },

  successWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  successTitle: { fontSize: 22, fontWeight: '800', color: Colors.text, marginTop: 20 },
  successSub: { fontSize: 14, color: Colors.textSecondary, marginTop: 8 },
});
