import { FastifyInstance } from "fastify";
import { eq, desc } from "drizzle-orm";
import { db } from "../database/connection";
import {
  orders,
  orderItems,
  products,
  users,
  insertOrderSchema,
  type Order,
  type NewOrder,
} from "../database/schema";

export async function orderRoutes(fastify: FastifyInstance) {
  // Get all orders with user and items
  fastify.get<{ Reply: any[] }>("/orders", async (request, reply) => {
    try {
      const allOrders = await db
        .select({
          id: orders.id,
          status: orders.status,
          totalAmount: orders.totalAmount,
          createdAt: orders.createdAt,
          user: {
            id: users.id,
            email: users.email,
            firstName: users.firstName,
            lastName: users.lastName,
          },
        })
        .from(orders)
        .leftJoin(users, eq(orders.userId, users.id))
        .orderBy(desc(orders.createdAt));

      return reply.send(allOrders);
    } catch (error) {
      return reply.status(500).send({ error: "Failed to fetch orders" });
    }
  });

  // Get order by ID with full details
  fastify.get<{ Params: { id: string }; Reply: any | { error: string } }>(
    "/orders/:id",
    async (request, reply) => {
      try {
        const { id } = request.params;

        // Get order with user details
        const orderWithUser = await db
          .select({
            id: orders.id,
            status: orders.status,
            totalAmount: orders.totalAmount,
            createdAt: orders.createdAt,
            user: {
              id: users.id,
              email: users.email,
              firstName: users.firstName,
              lastName: users.lastName,
            },
          })
          .from(orders)
          .leftJoin(users, eq(orders.userId, users.id))
          .where(eq(orders.id, id))
          .limit(1);

        if (orderWithUser.length === 0) {
          return reply.status(404).send({ error: "Order not found" });
        }

        // Get order items with product details
        const items = await db
          .select({
            id: orderItems.id,
            quantity: orderItems.quantity,
            pricePerItem: orderItems.pricePerItem,
            product: {
              id: products.id,
              name: products.name,
              description: products.description,
            },
          })
          .from(orderItems)
          .leftJoin(products, eq(orderItems.productId, products.id))
          .where(eq(orderItems.orderId, id));

        const result = {
          ...orderWithUser[0],
          items,
        };

        return reply.send(result);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch order" });
      }
    }
  );

  // Create new order with items (transaction)
  fastify.post<{
    Body: {
      userId: string;
      items: Array<{ productId: string; quantity: number }>;
    };
    Reply: any | { error: string };
  }>("/orders", async (request, reply) => {
    try {
      const { userId, items } = request.body;

      if (!items || items.length === 0) {
        return reply
          .status(400)
          .send({ error: "Order must have at least one item" });
      }

      // Start transaction
      const result = await db.transaction(async (tx) => {
        // Calculate total amount
        let totalAmount = 0;
        const orderItemsData = [];

        for (const item of items) {
          const product = await tx
            .select()
            .from(products)
            .where(eq(products.id, item.productId))
            .limit(1);

          if (product.length === 0) {
            throw new Error(`Product ${item.productId} not found`);
          }

          if (!product[0].isAvailable) {
            throw new Error(`Product ${product[0].name} is not available`);
          }

          const itemTotal = product[0].price * item.quantity;
          totalAmount += itemTotal;

          orderItemsData.push({
            productId: item.productId,
            quantity: item.quantity,
            pricePerItem: product[0].price,
          });
        }

        // Create order
        const newOrder = await tx
          .insert(orders)
          .values({
            userId,
            status: "pending",
            totalAmount,
          })
          .returning();

        // Create order items
        const orderItemsWithOrderId = orderItemsData.map((item) => ({
          ...item,
          orderId: newOrder[0].id,
        }));

        await tx.insert(orderItems).values(orderItemsWithOrderId);

        return newOrder[0];
      });

      return reply.status(201).send(result);
    } catch (error) {
      return reply.status(400).send({
        error:
          error instanceof Error ? error.message : "Failed to create order",
      });
    }
  });

  // Update order status
  fastify.put<{
    Params: { id: string };
    Body: { status: string };
    Reply: Order | { error: string };
  }>("/orders/:id/status", async (request, reply) => {
    try {
      const { id } = request.params;
      const { status } = request.body;

      const validStatuses = [
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
      ];
      if (!validStatuses.includes(status)) {
        return reply.status(400).send({ error: "Invalid status" });
      }

      const updatedOrder = await db
        .update(orders)
        .set({ status, updatedAt: new Date() })
        .where(eq(orders.id, id))
        .returning();

      if (updatedOrder.length === 0) {
        return reply.status(404).send({ error: "Order not found" });
      }

      return reply.send(updatedOrder[0]);
    } catch (error) {
      return reply.status(400).send({ error: "Failed to update order status" });
    }
  });
}
