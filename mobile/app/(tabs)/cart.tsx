import React, { useMemo } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { safeImage } from '@/lib/api';

export default function CartScreen() {
  const router = useRouter();
  const { cart, removeFromCart, clearCart, setCartQty } = useAuth();

  const total = useMemo(() => cart.reduce((sum, i) => sum + i.price * i.qty, 0), [cart]);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mon panier</Text>
        {cart.length > 0 ? (
          <Pressable onPress={clearCart} hitSlop={8}>
            <Text style={styles.clearText}>Vider</Text>
          </Pressable>
        ) : null}
      </View>

      {cart.length === 0 ? (
        <View style={styles.center}>
          <EmptyState icon="cart-outline" title="Votre panier est vide" subtitle="Ajoutez des articles pour commencer" />
          <View style={styles.ctaWrap}>
            <Button title="Découvrir le marché" onPress={() => router.push('/(tabs)')} icon="storefront-outline" />
          </View>
        </View>
      ) : (
        <>
          <FlatList
            data={cart}
            keyExtractor={(i) => String(i.product_id)}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <View style={styles.item}>
                <Image source={{ uri: safeImage(item.image_url, 'https://via.placeholder.com/100') }} style={styles.itemImg} contentFit="cover" transition={150} />
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName} numberOfLines={1}>{item.name}</Text>
                  <Text style={styles.itemShop} numberOfLines={1}>{item.shop_name}</Text>
                  <Text style={styles.itemPrice}>{item.price.toLocaleString('fr-FR')} FC</Text>
                  <View style={styles.qtyRow}>
                    <Pressable style={styles.qtyBtn} onPress={() => item.qty > 1 ? setCartQty(item.product_id, item.qty - 1) : removeFromCart(item.product_id)}>
                      <Ionicons name="remove" size={18} color={Colors.text} />
                    </Pressable>
                    <Text style={styles.qtyText}>{item.qty}</Text>
                    <Pressable style={styles.qtyBtn} onPress={() => setCartQty(item.product_id, item.qty + 1)}>
                      <Ionicons name="add" size={18} color={Colors.text} />
                    </Pressable>
                  </View>
                </View>
                <Pressable onPress={() => removeFromCart(item.product_id)} hitSlop={8} style={styles.trash}>
                  <Ionicons name="trash-outline" size={20} color={Colors.danger} />
                </Pressable>
              </View>
            )}
          />
          <View style={styles.footer}>
            <View style={styles.totalRow}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalValue}>{total.toLocaleString('fr-FR')} FC</Text>
            </View>
            <Button title="Passer commande" onPress={() => router.push('/checkout')} icon="arrow-forward" />
            <Text style={styles.footerNote}>Paiement à la livraison</Text>
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: Colors.text },
  clearText: { color: Colors.danger, fontSize: 14, fontWeight: '600' },
  center: { flex: 1, justifyContent: 'center', padding: 24 },
  ctaWrap: { marginTop: 24 },
  list: { padding: 16, paddingBottom: 8 },
  item: { flexDirection: 'row', backgroundColor: Colors.surface, borderRadius: Radius.lg, padding: 12, marginBottom: 12, gap: 12 },
  itemImg: { width: 80, height: 80, borderRadius: Radius.md, backgroundColor: Colors.surfaceMuted },
  itemInfo: { flex: 1 },
  itemName: { fontSize: 15, fontWeight: '700', color: Colors.text },
  itemShop: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  itemPrice: { fontSize: 15, fontWeight: '800', color: Colors.primary, marginTop: 6 },
  qtyRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 8 },
  qtyBtn: { width: 28, height: 28, borderRadius: Radius.sm, backgroundColor: Colors.surfaceMuted, alignItems: 'center', justifyContent: 'center' },
  qtyText: { fontSize: 15, fontWeight: '700', color: Colors.text, minWidth: 20, textAlign: 'center' },
  trash: { alignSelf: 'flex-start' },
  footer: { borderTopWidth: 1, borderTopColor: Colors.border, backgroundColor: Colors.surface, padding: 16, paddingBottom: 20 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  totalLabel: { fontSize: 16, color: Colors.textSecondary },
  totalValue: { fontSize: 20, fontWeight: '800', color: Colors.text },
  footerNote: { textAlign: 'center', color: Colors.textLight, fontSize: 12, marginTop: 10 },
});
