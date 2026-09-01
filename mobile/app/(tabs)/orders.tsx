import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { Colors, Radius, Spacing } from '@/constants/theme';
import * as api from '@/lib/api';
import type { Order } from '@/lib/types';

type Filter = 'active' | 'delivered';

const STATUS_COLORS: Record<string, string> = {
  pending: '#eab308',
  confirmed: '#009fe3',
  shipped: '#8b5cf6',
  delivered: '#10b981',
  cancelled: '#ef4444',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'En attente',
  confirmed: 'Confirmée',
  shipped: 'Expédiée',
  delivered: 'Livrée',
  cancelled: 'Annulée',
};

export default function OrdersScreen() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<Filter>('active');

  const loadOrders = useCallback(async () => {
    if (!user) return;
    try {
      const rows = await api.listOrdersForClient(user.id);
      setOrders(rows);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [user]);

  useFocusEffect(
    useCallback(() => {
      loadOrders();
    }, [loadOrders]),
  );

  useEffect(() => {
    if (user) {
      setLoading(true);
      loadOrders();
    }
  }, [user, loadOrders]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadOrders();
    setRefreshing(false);
  }, [loadOrders]);

  const activeOrders = orders.filter((o) => o.status !== 'delivered' && o.status !== 'cancelled');
  const deliveredOrders = orders.filter((o) => o.status === 'delivered' || o.status === 'cancelled');
  const shown = filter === 'active' ? activeOrders : deliveredOrders;

  if (!user) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.center}>
          <Text style={styles.message}>Connectez-vous pour voir vos commandes</Text>
        </View>
      </SafeAreaView>
    );
  }

  const renderOrder = ({ item }: { item: Order }) => {
    const statusColor = STATUS_COLORS[item.status] || Colors.textSecondary;
    const statusLabel = STATUS_LABELS[item.status] || item.status;
    const isDeliveredGroup = item.status === 'delivered' || item.status === 'cancelled';

    return (
      <View style={styles.card}>
        <Image
          source={{ uri: api.safeImage(item.product_image_url, 'https://via.placeholder.com/100') }}
          style={styles.cardImg}
          contentFit="cover"
          transition={150}
        />
        <View style={styles.cardInfo}>
          <Text style={styles.cardNumber}>Commande #{item.id}</Text>
          <Text style={styles.cardName} numberOfLines={1}>{item.product_name || 'Produit'}</Text>
          <Text style={styles.cardShop} numberOfLines={1}>
            <Ionicons name="storefront-outline" size={12} color={Colors.textLight} /> {item.shop_name || 'Boutique'}
          </Text>
          <Text style={styles.cardQty}>Qte: {item.quantity} - {Number(item.total_amount || 0).toLocaleString('fr-FR')} FC</Text>
          <View style={styles.cardFooter}>
            <View style={[styles.statusPill, { borderColor: statusColor }]}>
              <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
              <Text style={[styles.statusText, { color: statusColor }]}>{statusLabel}</Text>
            </View>
            {filter === 'active' && !isDeliveredGroup ? (
              <Pressable onPress={() => showDeliveryCode(item)} hitSlop={8} style={styles.actionBtn}>
                <Ionicons name="qr-code" size={20} color={Colors.primary} />
              </Pressable>
            ) : null}
          </View>
        </View>
      </View>
    );
  };

  const showDeliveryCode = useCallback((order: Order) => {
    Alert.alert(
      'Code de retrait',
      order.delivery_code ? `Code : ${order.delivery_code}` : 'Aucun code disponible pour cette commande.',
    );
  }, []);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mes commandes</Text>
      </View>

      <View style={styles.segmentRow}>
        <Pressable
          style={[styles.segment, filter === 'active' && styles.segmentActive]}
          onPress={() => setFilter('active')}
        >
          <Text style={[styles.segmentText, filter === 'active' && styles.segmentTextActive]}>En cours</Text>
        </Pressable>
        <Pressable
          style={[styles.segment, filter === 'delivered' && styles.segmentActive]}
          onPress={() => setFilter('delivered')}
        >
          <Text style={[styles.segmentText, filter === 'delivered' && styles.segmentTextActive]}>Livrées ({deliveredOrders.length})</Text>
        </Pressable>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : (
        <FlatList
          data={shown}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} tintColor={Colors.primary} />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <View style={styles.emptyIconWrap}>
                <Ionicons name="receipt-outline" size={40} color={Colors.textLight} />
              </View>
              <Text style={styles.emptyTitle}>Aucune commande</Text>
              <Text style={styles.emptySubtitle}>Vos commandes apparaîtront ici</Text>
            </View>
          }
          renderItem={renderOrder}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  header: { paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: Colors.text },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  message: { fontSize: 16, color: Colors.textSecondary },
  segmentRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 12,
    backgroundColor: Colors.surfaceMuted,
    borderRadius: Radius.md,
    padding: 4,
  },
  segment: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: Radius.sm,
    alignItems: 'center',
  },
  segmentActive: { backgroundColor: Colors.primary },
  segmentText: { fontSize: 14, fontWeight: '600', color: Colors.textSecondary },
  segmentTextActive: { color: '#fff' },
  list: { padding: 16, paddingTop: 4, paddingBottom: 24 },
  card: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: 12,
    marginBottom: 12,
    gap: 12,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardImg: { width: 64, height: 64, borderRadius: Radius.md, backgroundColor: Colors.surfaceMuted },
  cardInfo: { flex: 1 },
  cardNumber: { fontSize: 12, fontWeight: '700', color: Colors.textLight },
  cardName: { fontSize: 15, fontWeight: '700', color: Colors.text, marginTop: 2 },
  cardShop: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  cardQty: { fontSize: 13, fontWeight: '600', color: Colors.text, marginTop: 6 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderRadius: Radius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusText: { fontSize: 12, fontWeight: '600' },
  actionBtn: { width: 32, height: 32, borderRadius: Radius.sm, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center' },
  empty: { alignItems: 'center', paddingVertical: 60, gap: 4 },
  emptyIconWrap: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: Colors.surfaceMuted,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  emptyTitle: { fontSize: 17, fontWeight: '700', color: Colors.text },
  emptySubtitle: { fontSize: 13, color: Colors.textSecondary, marginTop: 6 },
});
