import { FastifyInstance } from "fastify";
import { eq } from "drizzle-orm";
import { db } from "../database/connection";
import {
  products,
  insertProductSchema,
  type Product,
  type NewProduct,
} from "../database/schema";

export async function productRoutes(fastify: FastifyInstance) {
  // Get all products
  fastify.get<{ Reply: Product[] }>("/products", async (request, reply) => {
    try {
      const allProducts = await db.select().from(products);
      return reply.send(allProducts);
    } catch (error) {
      return reply.status(500).send({ error: "Failed to fetch products" });
    }
  });

  // Get product by ID
  fastify.get<{ Params: { id: string }; Reply: Product | { error: string } }>(
    "/products/:id",
    async (request, reply) => {
      try {
        const { id } = request.params;
        const product = await db
          .select()
          .from(products)
          .where(eq(products.id, id))
          .limit(1);

        if (product.length === 0) {
          return reply.status(404).send({ error: "Product not found" });
        }

        return reply.send(product[0]);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch product" });
      }
    }
  );

  // Create new product
  fastify.post<{ Body: NewProduct; Reply: Product | { error: string } }>(
    "/products",
    async (request, reply) => {
      try {
        const validatedData = insertProductSchema.parse(request.body);
        const newProduct = await db
          .insert(products)
          .values(validatedData)
          .returning();

        return reply.status(201).send(newProduct[0]);
      } catch (error) {
        return reply.status(400).send({ error: "Invalid product data" });
      }
    }
  );

  // Update product
  fastify.put<{
    Params: { id: string };
    Body: Partial<NewProduct>;
    Reply: Product | { error: string };
  }>("/products/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const updateData = { ...request.body, updatedAt: new Date() };

      const updatedProduct = await db
        .update(products)
        .set(updateData)
        .where(eq(products.id, id))
        .returning();

      if (updatedProduct.length === 0) {
        return reply.status(404).send({ error: "Product not found" });
      }

      return reply.send(updatedProduct[0]);
    } catch (error) {
      return reply.status(400).send({ error: "Failed to update product" });
    }
  });

  // Delete product
  fastify.delete<{
    Params: { id: string };
    Reply: { success: boolean } | { error: string };
  }>("/products/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const deletedProduct = await db
        .delete(products)
        .where(eq(products.id, id))
        .returning();

      if (deletedProduct.length === 0) {
        return reply.status(404).send({ error: "Product not found" });
      }

      return reply.send({ success: true });
    } catch (error) {
      return reply.status(500).send({ error: "Failed to delete product" });
    }
  });
}
