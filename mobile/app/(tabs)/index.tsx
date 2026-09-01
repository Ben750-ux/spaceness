import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View, RefreshControl, Modal } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { ProductCard } from '@/components/ProductCard';
import { Colors, Radius, Spacing } from '@/constants/theme';
import * as api from '@/lib/api';
import type { Product } from '@/lib/types';

const CATEGORIES = ['Tous', 'Tech', 'Mode', 'Maison', 'Alimentaire', 'Beauté', 'Sport', 'Autre'];

export default function MarketScreen() {
  const router = useRouter();
  const { user, cartCount, signOut } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [category, setCategory] = useState('Tous');
  const [favIds, setFavIds] = useState<Set<number>>(new Set());
  const [menuOpen, setMenuOpen] = useState(false);

  const loadProducts = useCallback(async (cat: string) => {
    try {
      const [rows, favs] = await Promise.all([
        api.listProducts('', cat === 'Tous' ? '' : cat),
        user ? api.listFavorites(user.id) : Promise.resolve([]),
      ]);
      setProducts(rows);
      setFavIds(new Set(favs.map((f) => f.id)));
    } catch {
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadProducts(category);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadProducts(category);
    setRefreshing(false);
  }, [category, loadProducts]);

  const toggleFav = useCallback(async (product: Product) => {
    if (!user) return;
    const isFav = favIds.has(product.id);
    if (isFav) await api.removeFromFavorites(user.id, product.id);
    else await api.addToFavorites(user.id, product.id);
    setFavIds((prev) => {
      const next = new Set(prev);
      if (isFav) next.delete(product.id); else next.add(product.id);
      return next;
    });
  }, [user, favIds]);

  const handleLogout = async () => {
    setMenuOpen(false);
    await signOut();
    router.replace('/(auth)/login');
  };

  const initial = (user?.full_name || '?').trim().charAt(0).toUpperCase();

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => setMenuOpen(true)} hitSlop={8} style={styles.menuBtn}>
          <Ionicons name="menu" size={24} color="#fff" />
        </Pressable>
        <View style={styles.logoArea}>
          <Ionicons name="bag-handle" size={22} color="#fff" />
          <Text style={styles.logoText}>Spaceness</Text>
        </View>
        <Pressable onPress={() => router.push('/cart')} hitSlop={8} style={styles.cartBtn}>
          <Ionicons name="cart-outline" size={24} color="#fff" />
          {cartCount > 0 ? (
            <View style={styles.cartBadge}>
              <Text style={styles.cartBadgeText}>{cartCount > 9 ? '9+' : cartCount}</Text>
            </View>
          ) : null}
        </Pressable>
      </View>

      {/* Search bar */}
      <Pressable onPress={() => router.push('/search')} style={styles.searchBar}>
        <Ionicons name="search" size={18} color={Colors.textLight} />
        <Text style={styles.searchPlaceholder}>Rechercher un produit...</Text>
      </Pressable>

      {/* Greeting */}
      <View style={styles.greeting}>
        <Text style={styles.greetingHi}>Bonjour 👋</Text>
        <Text style={styles.greetingName}>{user?.full_name?.split(' ')[0] || 'Client'}</Text>
      </View>

      {/* Categories */}
      <View>
        <FlatList
          data={['Tous', ...CATEGORIES.filter((c) => c !== 'Tous')]}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(item) => item}
          contentContainerStyle={styles.catContent}
          renderItem={({ item }) => (
            <Pressable onPress={() => setCategory(item)} style={[styles.catChip, category === item && styles.catChipActive]}>
              <Text style={[styles.catText, category === item && styles.catTextActive]}>{item}</Text>
            </Pressable>
          )}
        />
      </View>

      {/* Products */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => String(item.id)}
          numColumns={2}
          columnWrapperStyle={styles.gridRow}
          contentContainerStyle={styles.gridContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="storefront-outline" size={48} color={Colors.textLight} />
              <Text style={styles.emptyText}>Aucun produit dans cette catégorie</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={styles.cardWrap}>
              <ProductCard product={item} isFavorite={favIds.has(item.id)} onToggleFavorite={() => toggleFav(item)} />
            </View>
          )}
        />
      )}

      {/* Menu modal */}
      <Modal visible={menuOpen} animationType="fade" transparent onRequestClose={() => setMenuOpen(false)}>
        <Pressable style={styles.overlay} onPress={() => setMenuOpen(false)} />
        <View style={styles.drawer}>
          <View style={styles.drawerHeader}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{initial}</Text>
            </View>
            <View>
              <Text style={styles.drawerName}>{user?.full_name || 'Client'}</Text>
              <Text style={styles.drawerEmail}>{user?.email}</Text>
            </View>
          </View>
          <DrawerItem icon="heart-outline" label="Favoris" onPress={() => { setMenuOpen(false); router.push('/favorites'); }} />
          <DrawerItem icon="time-outline" label="Historique" onPress={() => { setMenuOpen(false); router.push('/history'); }} />
          <DrawerItem icon="chatbubbles-outline" label="Contacter l'admin" onPress={() => { setMenuOpen(false); router.push('/contact'); }} />
          <View style={styles.drawerDivider} />
          <DrawerItem icon="log-out-outline" label="Se déconnecter" danger onPress={handleLogout} />
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function DrawerItem({ icon, label, onPress, danger }: { icon: any; label: string; onPress: () => void; danger?: boolean }) {
  return (
    <Pressable onPress={onPress} style={styles.drawerItem}>
      <Ionicons name={icon} size={22} color={danger ? Colors.danger : Colors.textSecondary} />
      <Text style={[styles.drawerItemText, danger && { color: Colors.danger }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  header: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.primary, paddingHorizontal: 16, paddingVertical: 16, gap: 12 },
  menuBtn: { width: 38, height: 38, borderRadius: Radius.full, backgroundColor: 'rgba(255,255,255,0.15)', alignItems: 'center', justifyContent: 'center' },
  logoArea: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8 },
  logoText: { color: '#fff', fontSize: 22, fontWeight: '900', letterSpacing: 0.3 },
  cartBtn: { width: 38, height: 38, borderRadius: Radius.full, backgroundColor: 'rgba(255,255,255,0.15)', alignItems: 'center', justifyContent: 'center' },
  cartBadge: { position: 'absolute', top: -4, right: -4, backgroundColor: Colors.danger, borderRadius: 9, minWidth: 17, height: 17, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 3 },
  cartBadgeText: { color: '#fff', fontSize: 10, fontWeight: '700' },
  searchBar: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, marginHorizontal: 16, marginTop: 16, paddingHorizontal: 14, height: 48, borderRadius: Radius.md, borderWidth: 1, borderColor: Colors.border, gap: 8 },
  searchPlaceholder: { color: Colors.textLight, fontSize: 15 },
  greeting: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 6 },
  greetingHi: { fontSize: 20, fontWeight: '800', color: Colors.text },
  greetingName: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  catContent: { paddingHorizontal: 16, paddingVertical: 10, gap: 8, paddingBottom: 14 },
  catChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: Radius.full, backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.border },
  catChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  catText: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary },
  catTextActive: { color: '#fff' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  gridContent: { paddingHorizontal: 16, paddingBottom: 24 },
  gridRow: { gap: 10, marginBottom: 10 },
  cardWrap: { flex: 1 },
  empty: { alignItems: 'center', paddingVertical: 60, gap: 12 },
  emptyText: { color: Colors.textSecondary, fontSize: 15 },
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)' },
  drawer: { position: 'absolute', top: 0, bottom: 0, left: 0, width: 280, backgroundColor: Colors.surface, paddingTop: 48, paddingHorizontal: 16 },
  drawerHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 24 },
  avatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: Colors.primary, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontSize: 22, fontWeight: '800' },
  drawerName: { fontSize: 17, fontWeight: '800', color: Colors.text },
  drawerEmail: { fontSize: 12, color: Colors.textSecondary },
  drawerItem: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 14 },
  drawerItemText: { fontSize: 15, color: Colors.text, fontWeight: '500' },
  drawerDivider: { height: 1, backgroundColor: Colors.border, marginVertical: 8 },
});
