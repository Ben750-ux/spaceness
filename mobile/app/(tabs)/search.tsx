import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, TextInput, View, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { ProductCard } from '@/components/ProductCard';
import { Colors, Radius } from '@/constants/theme';
import * as api from '@/lib/api';
import type { Product } from '@/lib/types';

export default function SearchScreen() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [favIds, setFavIds] = useState<Set<number>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const performSearch = useCallback(async (q: string, cat: string) => {
    setLoading(true);
    const [rows, favs] = await Promise.all([
      api.listProducts(q, cat),
      user ? api.listFavorites(user.id) : Promise.resolve([]),
    ]);
    setProducts(rows);
    setFavIds(new Set(favs.map((f) => f.id)));
    setLoading(false);
  }, [user]);

  useEffect(() => {
    const t = setTimeout(() => performSearch(query, category), 400);
    return () => clearTimeout(t);
  }, [query, category, performSearch]);

  const toggleFav = async (product: Product) => {
    if (!user) return;
    const isFav = favIds.has(product.id);
    if (isFav) await api.removeFromFavorites(user.id, product.id);
    else await api.addToFavorites(user.id, product.id);
    setFavIds((prev) => {
      const n = new Set(prev);
      if (isFav) n.delete(product.id); else n.add(product.id);
      return n;
    });
  };

  const categories = ['', 'Tech', 'Mode', 'Maison', 'Sport', 'Beauté', 'Autre'];

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recherche</Text>
      </View>

      <View style={styles.searchRow}>
        <View style={styles.inputWrap}>
          <Ionicons name="search" size={18} color={Colors.textLight} />
          <TextInput
            placeholder="Rechercher..."
            placeholderTextColor={Colors.textLight}
            value={query}
            onChangeText={setQuery}
            style={styles.input}
            autoCapitalize="none"
          />
          {query ? (
            <Pressable onPress={() => setQuery('')} hitSlop={8}>
              <Ionicons name="close-circle" size={18} color={Colors.textLight} />
            </Pressable>
          ) : null}
        </View>
        <Pressable onPress={() => setShowFilters(!showFilters)} style={[styles.filterBtn, showFilters && { backgroundColor: Colors.primary }]}>
          <Ionicons name="options-outline" size={20} color={showFilters ? '#fff' : Colors.primary} />
        </Pressable>
      </View>

      {showFilters ? (
        <View style={styles.filters}>
          <FlatList
            horizontal
            data={categories}
            keyExtractor={(c) => c || 'all'}
            contentContainerStyle={{ gap: 8, paddingHorizontal: 16 }}
            renderItem={({ item }) => (
              <Pressable onPress={() => setCategory(item)} style={[styles.catChip, category === item && styles.catChipActive]}>
                <Text style={[styles.catText, category === item && { color: '#fff' }]}>{item || 'Toutes'}</Text>
              </Pressable>
            )}
          />
        </View>
      ) : null}

      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.primary} /></View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(it) => String(it.id)}
          numColumns={2}
          columnWrapperStyle={styles.gridRow}
          contentContainerStyle={styles.gridContent}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Ionicons name="search-outline" size={48} color={Colors.textLight} />
              <Text style={styles.emptyText}>{query ? 'Aucun résultat' : 'Recherchez des produits'}</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={styles.cardWrap}>
              <ProductCard product={item} isFavorite={favIds.has(item.id)} onToggleFavorite={() => toggleFav(item)} />
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: Colors.text },
  searchRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, gap: 8, marginBottom: 8 },
  inputWrap: { flex: 1, flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.border, borderRadius: Radius.md, paddingHorizontal: 12, height: 46, gap: 8 },
  input: { flex: 1, fontSize: 15, color: Colors.text, paddingVertical: 0 },
  filterBtn: { width: 46, height: 46, borderRadius: Radius.md, borderWidth: 1.5, borderColor: Colors.primary, alignItems: 'center', justifyContent: 'center' },
  filters: { paddingVertical: 8 },
  catChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: Radius.full, backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.border },
  catChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  catText: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  gridContent: { padding: 16, paddingBottom: 24 },
  gridRow: { gap: 10, marginBottom: 10 },
  cardWrap: { flex: 1 },
  empty: { alignItems: 'center', paddingVertical: 60, gap: 12 },
  emptyText: { color: Colors.textSecondary, fontSize: 15 },
});
