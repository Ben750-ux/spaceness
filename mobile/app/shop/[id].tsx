import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/context/AuthContext';
import { Colors, Radius, Spacing } from '@/constants/theme';
import * as api from '@/lib/api';
import type { Product, Shop } from '@/lib/types';
import { ProductCard } from '@/components/ProductCard';

export default function ShopDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const shopId = Number(id);
  const router = useRouter();
  const { user } = useAuth();

  const [shop, setShop] = useState<Shop | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscribed, setSubscribed] = useState(false);
  const [togglingSub, setTogglingSub] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set());
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (!shopId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      const [shopData, productsData] = await Promise.all([
        api.getShopDetails(shopId),
        api.listShopProducts(shopId),
      ]);
      if (cancelled) return;
      setShop(shopData);
      setProducts(productsData);
      setLoading(false);

      if (user) {
        const [isSub, favs] = await Promise.all([
          api.isSubscribedToShop(user.id, shopId),
          api.listFavorites(user.id),
        ]);
        if (!cancelled) {
          setSubscribed(isSub);
          setFavoriteIds(new Set(favs.map((f) => f.id)));
        }
      }
    })();
    return () => { cancelled = true; };
  }, [shopId, user?.id]);

  const toggleSubscription = useCallback(async () => {
    if (!user) {
      Alert.alert('Connexion requise', 'Veuillez vous connecter');
      return;
    }
    if (togglingSub) return;
    setTogglingSub(true);
    try {
      if (subscribed) {
        const ok = await api.unsubscribeFromShop(user.id, shopId);
        if (mountedRef.current && ok) setSubscribed(false);
      } else {
        const ok = await api.subscribeToShop(user.id, shopId);
        if (mountedRef.current && ok) setSubscribed(true);
      }
    } finally {
      if (mountedRef.current) setTogglingSub(false);
    }
  }, [user, shopId, subscribed, togglingSub]);

  const toggleFavorite = useCallback(async (product: Product) => {
    if (!user) return;
    const isFav = favoriteIds.has(product.id);
    if (isFav) await api.removeFromFavorites(user.id, product.id);
    else await api.addToFavorites(user.id, product.id);
    setFavoriteIds((prev) => {
      const next = new Set(prev);
      if (isFav) next.delete(product.id);
      else next.add(product.id);
      return next;
    });
  }, [user, favoriteIds]);

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (!shop) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="chevron-back" size={22} color={Colors.text} />
          </Pressable>
          <Text style={styles.headerTitle}>Boutique introuvable</Text>
          <View style={{ width: 38 }} />
        </View>
        <View style={styles.center}>
          <Text style={{ color: Colors.textSecondary }}>Cette boutique n'existe pas.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const renderHeader = () => (
    <View style={styles.headerContent}>
      <View style={styles.bannerWrap}>
        <Image
          source={{ uri: api.safeImage(shop.banner_url) || undefined }}
          style={styles.banner}
          contentFit="cover"
          transition={200}
        />
        <View style={styles.logoWrap}>
          <Image
            source={{ uri: api.safeImage(shop.logo_url) || undefined }}
            style={styles.logo}
            contentFit="cover"
            transition={200}
          />
        </View>
      </View>

      <View style={styles.infoSection}>
        <Text style={styles.shopName}>{shop.shop_name}</Text>
        {shop.description ? (
          <Text style={styles.shopDesc} numberOfLines={2}>{shop.description}</Text>
        ) : null}

        {shop.contact_info ? (
          <View style={styles.contactRow}>
            <Ionicons name="call-outline" size={16} color={Colors.textSecondary} />
            <Text style={styles.contactText} numberOfLines={1}>{shop.contact_info}</Text>
          </View>
        ) : null}

        <Pressable
          onPress={toggleSubscription}
          disabled={togglingSub}
          style={[
            styles.subBtn,
            { backgroundColor: subscribed ? Colors.secondary : Colors.primary },
          ]}
        >
          {togglingSub ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Ionicons
                name={subscribed ? 'checkmark-circle' : 'notifications-outline'}
                size={20}
                color="#fff"
              />
              <Text style={styles.subBtnText}>
                {subscribed ? 'Abonné' : "S'abonner"}
              </Text>
            </>
          )}
        </Pressable>
      </View>

      <View style={styles.sectionHeader}>
        <Ionicons name="storefront-outline" size={18} color={Colors.text} />
        <Text style={styles.sectionTitle}>Produits</Text>
        <Text style={styles.productCount}>{products.length}</Text>
      </View>
    </View>
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="storefront-outline" size={56} color={Colors.textLight} />
      <Text style={styles.emptyText}>Aucun produit dans cette boutique</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={22} color={Colors.text} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {shop.shop_name}
        </Text>
        <View style={{ width: 38 }} />
      </View>

      <FlatList
        data={products}
        keyExtractor={(item) => String(item.id)}
        numColumns={2}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={!loading ? renderEmpty : null}
        contentContainerStyle={styles.listContent}
        columnWrapperStyle={styles.columnWrapper}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <View style={styles.cardWrap}>
            <ProductCard
              product={item}
              isFavorite={favoriteIds.has(item.id)}
              onToggleFavorite={() => toggleFavorite(item)}
            />
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: Colors.text,
    textAlign: 'center',
    marginHorizontal: Spacing.sm,
  },
  headerContent: {
    backgroundColor: Colors.surface,
    marginBottom: Spacing.sm,
  },
  bannerWrap: {
    width: '100%',
    height: 150,
    backgroundColor: Colors.surfaceMuted,
  },
  banner: {
    width: '100%',
    height: '100%',
  },
  logoWrap: {
    width: 76,
    height: 76,
    borderRadius: 38,
    overflow: 'hidden',
    borderWidth: 3,
    borderColor: Colors.surface,
    backgroundColor: Colors.surfaceMuted,
    alignSelf: 'center',
    marginTop: -38,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  infoSection: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.lg,
    alignItems: 'center',
    gap: Spacing.sm,
  },
  shopName: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.text,
    textAlign: 'center',
  },
  shopDesc: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: Spacing.xs,
  },
  contactText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  subBtn: {
    width: '100%',
    height: 50,
    borderRadius: Radius.md,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginTop: Spacing.sm,
  },
  subBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: Colors.text,
    flex: 1,
  },
  productCount: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    backgroundColor: Colors.surfaceMuted,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: Radius.full,
    overflow: 'hidden',
  },
  listContent: {
    padding: Spacing.lg,
    paddingTop: 0,
  },
  columnWrapper: {
    gap: 10,
    marginBottom: 10,
  },
  cardWrap: {
    flex: 1,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
    gap: Spacing.md,
  },
  emptyText: {
    fontSize: 15,
    color: Colors.textLight,
    fontWeight: '500',
  },
});
