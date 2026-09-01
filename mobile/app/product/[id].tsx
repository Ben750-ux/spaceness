import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
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
import type { Product, Review } from '@/lib/types';

function Stars({ rating, size = 16 }: { rating: number; size?: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.3 && rating - full < 0.8;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
      {Array.from({ length: full }).map((_, i) => (
        <Ionicons key={`f${i}`} name="star" size={size} color={Colors.accent} />
      ))}
      {half && <Ionicons name="star-half" size={size} color={Colors.accent} />}
      {Array.from({ length: empty }).map((_, i) => (
        <Ionicons key={`e${i}`} name="star-outline" size={size} color={Colors.accent} />
      ))}
    </View>
  );
}

export default function ProductDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const productId = Number(id);
  const router = useRouter();
  const { user, addToCart } = useAuth();

  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [rating, setRating] = useState(0);
  const [reviewCount, setReviewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [isFavorite, setIsFavorite] = useState(false);
  const [qty, setQty] = useState(1);
  const [cartMessage, setCartMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      const [prod, revData] = await Promise.all([
        api.getProductById(productId),
        api.getProductReviews(productId),
      ]);
      if (cancelled) return;
      setProduct(prod);
      setReviews(revData.reviews);
      setRating(revData.rating);
      setReviewCount(revData.count);
      setLoading(false);

      if (user) {
        api.addToHistory(user.id, productId);
        const favs = await api.listFavorites(user.id);
        if (!cancelled) setIsFavorite(favs.some((f) => f.id === productId));
      }
    })();
    return () => { cancelled = true; };
  }, [productId, user?.id]);

  const toggleFavorite = useCallback(async () => {
    if (!user || !product) return;
    if (isFavorite) await api.removeFromFavorites(user.id, product.id);
    else await api.addToFavorites(user.id, product.id);
    setIsFavorite((prev) => !prev);
  }, [user, product, isFavorite]);

  const handleAddToCart = useCallback(() => {
    if (!product) return;
    const res = addToCart({
      product_id: product.id,
      name: product.name,
      price: product.price,
      qty,
      image_url: product.image_url,
      shop_name: product.shop_name,
      shop_id: product.shop_id,
      stock: product.stock,
    });
    if (res.ok) {
      setCartMessage('Ajout\u00e9 \u2713');
      setTimeout(() => setCartMessage(null), 2000);
    } else {
      setCartMessage(res.message);
      setTimeout(() => setCartMessage(null), 3000);
    }
  }, [product, qty, addToCart]);

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (!product) {
    return (
      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="chevron-back" size={22} color={Colors.text} />
          </Pressable>
          <Text style={styles.headerTitle}>Produit introuvable</Text>
          <View style={{ width: 38 }} />
        </View>
        <View style={styles.center}>
          <Text style={{ color: Colors.textSecondary }}>Ce produit n\u2019existe pas.</Text>
        </View>
      </SafeAreaView>
    );
  }

  const images = [product.image_url, product.image_url_2, product.image_url_3].filter(Boolean) as string[];
  const hasMultiple = images.length > 1;

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={22} color={Colors.text} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {product.name}
        </Text>
        <Pressable onPress={toggleFavorite} style={styles.backBtn}>
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={22}
            color={isFavorite ? Colors.danger : Colors.text}
          />
        </Pressable>
      </View>

      <View style={styles.body}>
        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}>
          <View style={styles.imageContainer}>
            <Image
              source={{ uri: api.safeImage(images[selectedImage]) || undefined }}
              style={styles.mainImage}
              contentFit="cover"
              transition={200}
            />
          </View>

          {hasMultiple && (
            <View style={styles.thumbRow}>
              {images.map((img, i) => (
                <Pressable
                  key={i}
                  onPress={() => setSelectedImage(i)}
                  style={[styles.thumb, selectedImage === i && styles.thumbActive]}
                >
                  <Image
                    source={{ uri: api.safeImage(img) || undefined }}
                    style={styles.thumbImg}
                    contentFit="cover"
                  />
                </Pressable>
              ))}
            </View>
          )}

          <View style={styles.infoSection}>
            {product.category ? (
              <View style={styles.categoryPill}>
                <Text style={styles.categoryText}>{product.category}</Text>
              </View>
            ) : null}

            <Text style={styles.productName}>{product.name}</Text>

            {product.shop_name ? (
              <Pressable onPress={() => router.push(`/shop/${product.shop_id}`)} style={styles.shopRow}>
                <Ionicons name="storefront-outline" size={14} color={Colors.textSecondary} />
                <Text style={styles.shopName}>{product.shop_name}</Text>
              </Pressable>
            ) : null}

            <Text style={styles.price}>{product.price.toLocaleString('fr-FR')} FC</Text>

            <View style={styles.stockRow}>
              {product.stock > 0 ? (
                <>
                  <View style={styles.stockDotGreen} />
                  <Text style={styles.stockTextGreen}>En stock : {product.stock}</Text>
                </>
              ) : (
                <>
                  <View style={styles.stockDotRed} />
                  <Text style={styles.stockTextRed}>Rupture de stock</Text>
                </>
              )}
            </View>

            {reviewCount > 0 && (
              <View style={styles.ratingRow}>
                <Stars rating={rating} />
                <Text style={styles.ratingLabel}>
                  {rating.toFixed(1)} ({reviewCount} avis)
                </Text>
              </View>
            )}
          </View>

          {product.description ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Description</Text>
              <Text style={styles.descriptionText}>{product.description}</Text>
            </View>
          ) : null}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Avis</Text>
            {reviews.length === 0 ? (
              <Text style={styles.emptyReviews}>Aucun avis</Text>
            ) : (
              reviews.map((r, i) => (
                <View key={r.id || i} style={styles.reviewCard}>
                  <View style={styles.reviewHeader}>
                    <Text style={styles.reviewUser}>{r.user_name || 'Anonyme'}</Text>
                    <Stars rating={r.rating} size={13} />
                  </View>
                  {r.comment ? <Text style={styles.reviewComment}>{r.comment}</Text> : null}
                </View>
              ))
            )}
          </View>
        </ScrollView>
      </View>

      <View style={styles.footer}>
        {cartMessage && (
          <Text style={[styles.cartMsg, { color: cartMessage === 'Ajout\u00e9 \u2713' ? Colors.secondary : Colors.danger }]}>
            {cartMessage}
          </Text>
        )}
        <View style={styles.footerRow}>
          <View style={styles.qtySelector}>
            <Pressable
              onPress={() => setQty((q) => Math.max(1, q - 1))}
              style={styles.qtyBtn}
            >
              <Ionicons name="remove" size={18} color={Colors.text} />
            </Pressable>
            <Text style={styles.qtyValue}>{qty}</Text>
            <Pressable
              onPress={() => setQty((q) => Math.min(product.stock || 99, q + 1))}
              style={styles.qtyBtn}
            >
              <Ionicons name="add" size={18} color={Colors.text} />
            </Pressable>
          </View>

          <Pressable
            style={[styles.addCartBtn, product.stock <= 0 && { opacity: 0.5 }]}
            onPress={handleAddToCart}
            disabled={product.stock <= 0}
          >
            <Ionicons name="cart-outline" size={20} color="#fff" />
            <Text style={styles.addCartText}>Ajouter au panier</Text>
          </Pressable>
        </View>
      </View>
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
  body: { flex: 1 },
  imageContainer: {
    width: '100%',
    backgroundColor: Colors.surface,
  },
  mainImage: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: Colors.surfaceMuted,
  },
  thumbRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.surface,
  },
  thumb: {
    width: 64,
    height: 64,
    borderRadius: Radius.sm,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  thumbActive: {
    borderColor: Colors.primary,
  },
  thumbImg: {
    width: 64,
    height: 64,
    backgroundColor: Colors.surfaceMuted,
  },
  infoSection: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.lg,
    gap: Spacing.sm,
    backgroundColor: Colors.surface,
  },
  categoryPill: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: Radius.full,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primary,
    textTransform: 'uppercase',
  },
  productName: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.text,
    lineHeight: 28,
  },
  shopName: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  shopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  price: {
    fontSize: 24,
    fontWeight: '800',
    color: Colors.primary,
    marginTop: Spacing.xs,
  },
  stockRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: Spacing.xs,
  },
  stockDotGreen: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.secondary,
  },
  stockTextGreen: {
    fontSize: 13,
    color: Colors.secondary,
    fontWeight: '600',
  },
  stockDotRed: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.danger,
  },
  stockTextRed: {
    fontSize: 13,
    color: Colors.danger,
    fontWeight: '600',
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: Spacing.xs,
  },
  ratingLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  section: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.sm,
    gap: Spacing.sm,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: Colors.text,
  },
  descriptionText: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  emptyReviews: {
    fontSize: 14,
    color: Colors.textLight,
    paddingVertical: Spacing.lg,
  },
  reviewCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  reviewUser: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.text,
  },
  reviewComment: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
  },
  footer: {
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    paddingBottom: Spacing.xl,
  },
  cartMsg: {
    textAlign: 'center',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: Spacing.xs,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  qtySelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceMuted,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  qtyBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qtyValue: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.text,
    minWidth: 32,
    textAlign: 'center',
  },
  addCartBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.primary,
    height: 48,
    borderRadius: Radius.md,
    gap: 8,
  },
  addCartText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
});
