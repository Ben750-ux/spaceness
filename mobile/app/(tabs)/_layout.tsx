import { Tabs } from 'expo-router';
import { Redirect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Text, View } from 'react-native';
import { useAuth } from '@/context/AuthContext';
import { Colors } from '@/constants/theme';

function CartBadge({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <View style={{ position: 'absolute', top: -2, right: -8, backgroundColor: Colors.danger, borderRadius: 9, minWidth: 18, height: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 }}>
      <Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>{count > 9 ? '9+' : count}</Text>
    </View>
  );
}

export default function TabsLayout() {
  const { user, loading, cartCount } = useAuth();

  if (!loading && (!user || user.role !== 'client')) {
    return <Redirect href="/(auth)/login" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textLight,
        tabBarStyle: { height: 62, paddingBottom: 8, paddingTop: 6, backgroundColor: Colors.surface, borderTopColor: Colors.border },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Marché', tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? 'storefront' : 'storefront-outline'} size={size} color={color} /> }} />
      <Tabs.Screen name="search" options={{ title: 'Recherche', tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? 'search' : 'search-outline'} size={size} color={color} /> }} />
      <Tabs.Screen name="cart" options={{ title: 'Panier', tabBarIcon: ({ color, size, focused }) => (
        <View>
          <Ionicons name={focused ? 'cart' : 'cart-outline'} size={size} color={color} />
          <CartBadge count={cartCount} />
        </View>
      ) }} />
      <Tabs.Screen name="orders" options={{ title: 'Commandes', tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? 'receipt' : 'receipt-outline'} size={size} color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Profil', tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? 'person' : 'person-outline'} size={size} color={color} /> }} />
    </Tabs>
  );
}
