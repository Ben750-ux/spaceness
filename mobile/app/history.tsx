import React, { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { Colors, Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import type { Product } from '@/lib/types';
import { ProductCard } from '@/components/ProductCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { ScreenHeader } from '@/components/ui/Screen';

export default function HistoryScreen() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    const data = await api.listHistory(user.id);
    setProducts(data);
    setLoading(false);
  }, [user?.id]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const handleClear = async () => {
    if (!user?.id) return;
    await api.clearHistory(user.id);
    setProducts([]);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <ScreenHeader title="Historique" />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <ScreenHeader
        title="Historique"
        right={
          products.length > 0 ? (
            <Pressable onPress={handleClear} hitSlop={8}>
              <Text style={styles.clearBtn}>Effacer</Text>
            </Pressable>
          ) : undefined
        }
      />
      {products.length === 0 ? (
        <EmptyState icon="time-outline" title="Aucun historique" subtitle="Les produits vus apparaîtront ici" />
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => String(item.id)}
          numColumns={2}
          contentContainerStyle={styles.list}
          columnWrapperStyle={styles.row}
          renderItem={({ item }) => (
            <View style={styles.col}>
              <ProductCard product={item} />
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  clearBtn: { color: Colors.danger, fontSize: 14, fontWeight: '600' },
  list: { padding: Spacing.lg },
  row: { gap: 10 },
  col: { flex: 1, marginBottom: 10 },
});
