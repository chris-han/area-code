import { FastifyInstance } from "fastify";
import { eq } from "drizzle-orm";
import { db } from "../database/connection";
import {
  foo,
  insertFooSchema,
  selectFooSchema,
  type Foo,
  type NewFoo,
} from "../database/schema";

export async function fooRoutes(fastify: FastifyInstance) {
  // Get all foo items
  fastify.get<{ Reply: Foo[] | { error: string } }>(
    "/foo",
    async (request, reply) => {
      try {
        const allFoo = await db.select().from(foo);
        return reply.send(allFoo);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch foo items" });
      }
    }
  );

  // Get foo by ID
  fastify.get<{ Params: { id: string }; Reply: Foo | { error: string } }>(
    "/foo/:id",
    async (request, reply) => {
      try {
        const { id } = request.params;
        const fooItem = await db
          .select()
          .from(foo)
          .where(eq(foo.id, id))
          .limit(1);

        if (fooItem.length === 0) {
          return reply.status(404).send({ error: "Foo not found" });
        }

        return reply.send(fooItem[0]);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch foo" });
      }
    }
  );

  // Create new foo
  fastify.post<{ Body: NewFoo; Reply: Foo | { error: string } }>(
    "/foo",
    async (request, reply) => {
      try {
        const validatedData = insertFooSchema.parse(request.body);
        const newFoo = await db
          .insert(foo)
          .values(validatedData)
          .returning();

        return reply.status(201).send(newFoo[0]);
      } catch (error) {
        return reply.status(400).send({ error: "Invalid foo data" });
      }
    }
  );

  // Update foo
  fastify.put<{
    Params: { id: string };
    Body: Partial<NewFoo>;
    Reply: Foo | { error: string };
  }>("/foo/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const updateData = { ...request.body, updatedAt: new Date() };

      const updatedFoo = await db
        .update(foo)
        .set(updateData)
        .where(eq(foo.id, id))
        .returning();

      if (updatedFoo.length === 0) {
        return reply.status(404).send({ error: "Foo not found" });
      }

      return reply.send(updatedFoo[0]);
    } catch (error) {
      return reply.status(400).send({ error: "Failed to update foo" });
    }
  });

  // Delete foo
  fastify.delete<{
    Params: { id: string };
    Reply: { success: boolean } | { error: string };
  }>("/foo/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const deletedFoo = await db
        .delete(foo)
        .where(eq(foo.id, id))
        .returning();

      if (deletedFoo.length === 0) {
        return reply.status(404).send({ error: "Foo not found" });
      }

      return reply.send({ success: true });
    } catch (error) {
      return reply.status(500).send({ error: "Failed to delete foo" });
    }
  });
} 