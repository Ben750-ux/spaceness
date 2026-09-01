import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Colors, Radius, Spacing } from '@/constants/theme';
import type { Product } from '@/lib/types';
import { safeImage } from '@/lib/api';

interface ProductCardProps {
  product: Product;
  isFavorite?: boolean;
  onToggleFavorite?: () => void;
  onPress?: () => void;
  compact?: boolean;
}

const PLACEHOLDER = 'https://via.placeholder.com/400?text=Produit';

export const ProductCard: React.FC<ProductCardProps> = ({ product, isFavorite, onToggleFavorite, onPress, compact }) => {
  const router = useRouter();
  const handlePress = onPress ?? (() => router.push(`/product/${product.id}`));

  return (
    <Pressable onPress={handlePress} style={({ pressed }) => [styles.card, pressed && { opacity: 0.92, transform: [{ scale: 0.98 }] }]}>
      <View style={styles.imageWrap}>
        <Image source={{ uri: safeImage(product.image_url, PLACEHOLDER) }} style={styles.image} contentFit="cover" transition={200} />
        {product.category ? (
          <View style={styles.categoryBadge}>
            <Text style={styles.categoryText} numberOfLines={1}>{product.category}</Text>
          </View>
        ) : null}
        {onToggleFavorite ? (
          <Pressable onPress={onToggleFavorite} hitSlop={8} style={styles.favBtn}>
            <Ionicons name={isFavorite ? 'heart' : 'heart-outline'} size={20} color={isFavorite ? Colors.danger : '#fff'} />
          </Pressable>
        ) : null}
        <View style={[styles.stockBadge, product.stock <= 0 && styles.stockBadgeOut]}>
          <Text style={styles.stockText}>{product.stock > 0 ? `En stock: ${product.stock}` : 'Rupture'}</Text>
        </View>
      </View>
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={1}>{product.name}</Text>
        {product.shop_name ? <Text style={styles.shop} numberOfLines={1}>{product.shop_name}</Text> : null}
        <View style={styles.priceRow}>
          <Text style={styles.price}>{product.price.toLocaleString('fr-FR')} FC</Text>
          {product.rating ? (
            <View style={styles.rating}>
              <Ionicons name="star" size={14} color={Colors.accent} />
              <Text style={styles.ratingText}>{Number(product.rating).toFixed(1)}</Text>
            </View>
          ) : null}
        </View>
      </View>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  imageWrap: { width: '100%', aspectRatio: 1, backgroundColor: Colors.surfaceMuted },
  image: { width: '100%', height: '100%' },
  categoryBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: 'rgba(0,159,227,0.9)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: Radius.full,
    maxWidth: '60%',
  },
  categoryText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  favBtn: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.35)',
    width: 34,
    height: 34,
    borderRadius: Radius.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stockBadge: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    backgroundColor: 'rgba(16,185,129,0.92)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: Radius.full,
  },
  stockBadgeOut: { backgroundColor: 'rgba(239,68,68,0.92)' },
  stockText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  info: { padding: Spacing.md },
  name: { fontSize: 15, fontWeight: '700', color: Colors.text },
  shop: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  priceRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 },
  price: { fontSize: 16, fontWeight: '800', color: Colors.primary },
  rating: { flexDirection: 'row', alignItems: 'center' },
  ratingText: { fontSize: 13, color: Colors.textSecondary, marginLeft: 2, fontWeight: '600' },
});
