import { useMutation, useQuery } from "@tanstack/react-query";
import {
  createPromoClaim,
  getActivePromotions,
  getMe,
  getMyOrders,
  getMyPromo,
  listAdminClaims,
  listAdminOrders,
  placeOrder,
} from "../lib/api";
import { queryClient } from "../lib/queryClient";
import { useAuth } from "./useAuth";

// Cache keys. The user's id is part of them, so one person never sees another's cached data.
export const keys = {
  me: (userId) => ["me", userId],
  orders: (userId) => ["orders", userId],
  promo: (userId) => ["promo", userId],
  admin: ["admin"],
  promotions: ["promotions"],
};

// Starts loading everything the profile shows, right after sign-in, so it is ready when it is opened.
export function prefetchUserData(userId) {
  queryClient.prefetchQuery({ queryKey: keys.me(userId), queryFn: getMe });
  queryClient.prefetchQuery({ queryKey: keys.orders(userId), queryFn: getMyOrders });
  queryClient.prefetchQuery({ queryKey: keys.promo(userId), queryFn: getMyPromo });
}

function useUserQuery(key, queryFn) {
  const { user } = useAuth();
  return useQuery({ queryKey: key(user?.id), queryFn, enabled: Boolean(user) });
}

export const useMe = () => useUserQuery(keys.me, getMe);
export const useMyOrders = () => useUserQuery(keys.orders, getMyOrders);
export const useMyPromo = () => useUserQuery(keys.promo, getMyPromo);

// Promotions that are open for everyone right now. The same for every visitor, so signed out is fine.
export const useActivePromotions = () =>
  useQuery({ queryKey: keys.promotions, queryFn: getActivePromotions, staleTime: 60_000 });

// The admin queue changes under you as other people submit things, so it is always refreshed on open.
export function useAdminList(section, status) {
  return useQuery({
    queryKey: [...keys.admin, section, status],
    queryFn: () => (section === "payments" ? listAdminOrders(status) : listAdminClaims(status)),
    staleTime: 0,
  });
}

// Everything that a payment, a promo claim or an admin decision can change.
function refreshUserData() {
  return Promise.all(["me", "orders", "promo"].map((name) => queryClient.invalidateQueries({ queryKey: [name] })));
}

export const useSubmitOrder = () => useMutation({ mutationFn: placeOrder, onSuccess: refreshUserData });

export const useSubmitPromoClaim = () => useMutation({ mutationFn: createPromoClaim, onSuccess: refreshUserData });

// `decide` is a function that makes the request, e.g. () => approveOrder(id, cents).
// The mutation finishes only after the lists have been reloaded, so the card never lingers.
export const useAdminDecision = () =>
  useMutation({
    mutationFn: (decide) => decide(),
    onSuccess: () => Promise.all([queryClient.invalidateQueries({ queryKey: keys.admin }), refreshUserData()]),
  });
