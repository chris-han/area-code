import { FastifyInstance } from "fastify";
import { eq, desc } from "drizzle-orm";
import { db } from "../database/connection";
import {
  bar,
  foo,
  insertBarSchema,
  type Bar,
  type NewBar,
} from "../database/schema";

export async function barRoutes(fastify: FastifyInstance) {
  // Get all bar items with foo details
  fastify.get<{ Reply: any[] | { error: string } }>(
    "/bar",
    async (request, reply) => {
      try {
        const allBar = await db
          .select({
            id: bar.id,
            value: bar.value,
            label: bar.label,
            notes: bar.notes,
            isEnabled: bar.isEnabled,
            createdAt: bar.createdAt,
            foo: {
              id: foo.id,
              name: foo.name,
              description: foo.description,
              status: foo.status,
            },
          })
          .from(bar)
          .leftJoin(foo, eq(bar.fooId, foo.id))
          .orderBy(desc(bar.createdAt));

        return reply.send(allBar);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch bar items" });
      }
    }
  );

  // Get bar by ID with foo details
  fastify.get<{ Params: { id: string }; Reply: any | { error: string } }>(
    "/bar/:id",
    async (request, reply) => {
      try {
        const { id } = request.params;

        const barWithFoo = await db
          .select({
            id: bar.id,
            value: bar.value,
            label: bar.label,
            notes: bar.notes,
            isEnabled: bar.isEnabled,
            createdAt: bar.createdAt,
            updatedAt: bar.updatedAt,
            foo: {
              id: foo.id,
              name: foo.name,
              description: foo.description,
              status: foo.status,
            },
          })
          .from(bar)
          .leftJoin(foo, eq(bar.fooId, foo.id))
          .where(eq(bar.id, id))
          .limit(1);

        if (barWithFoo.length === 0) {
          return reply.status(404).send({ error: "Bar not found" });
        }

        return reply.send(barWithFoo[0]);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch bar" });
      }
    }
  );

  // Create new bar
  fastify.post<{ Body: NewBar; Reply: Bar | { error: string } }>(
    "/bar",
    async (request, reply) => {
      try {
        const validatedData = insertBarSchema.parse(request.body);
        
        // Verify that foo exists
        const fooExists = await db
          .select()
          .from(foo)
          .where(eq(foo.id, validatedData.fooId))
          .limit(1);

        if (fooExists.length === 0) {
          return reply.status(400).send({ error: "Referenced foo does not exist" });
        }

        const newBar = await db
          .insert(bar)
          .values(validatedData)
          .returning();

        return reply.status(201).send(newBar[0]);
      } catch (error) {
        return reply.status(400).send({ error: "Invalid bar data" });
      }
    }
  );

  // Update bar
  fastify.put<{
    Params: { id: string };
    Body: Partial<NewBar>;
    Reply: Bar | { error: string };
  }>("/bar/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const updateData = { ...request.body, updatedAt: new Date() };

      // If updating fooId, verify that foo exists
      if (updateData.fooId) {
        const fooExists = await db
          .select()
          .from(foo)
          .where(eq(foo.id, updateData.fooId))
          .limit(1);

        if (fooExists.length === 0) {
          return reply.status(400).send({ error: "Referenced foo does not exist" });
        }
      }

      const updatedBar = await db
        .update(bar)
        .set(updateData)
        .where(eq(bar.id, id))
        .returning();

      if (updatedBar.length === 0) {
        return reply.status(404).send({ error: "Bar not found" });
      }

      return reply.send(updatedBar[0]);
    } catch (error) {
      return reply.status(400).send({ error: "Failed to update bar" });
    }
  });

  // Delete bar
  fastify.delete<{
    Params: { id: string };
    Reply: { success: boolean } | { error: string };
  }>("/bar/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const deletedBar = await db
        .delete(bar)
        .where(eq(bar.id, id))
        .returning();

      if (deletedBar.length === 0) {
        return reply.status(404).send({ error: "Bar not found" });
      }

      return reply.send({ success: true });
    } catch (error) {
      return reply.status(500).send({ error: "Failed to delete bar" });
    }
  });

  // Get bars by foo ID
  fastify.get<{ Params: { fooId: string }; Reply: Bar[] | { error: string } }>(
    "/foo/:fooId/bars",
    async (request, reply) => {
      try {
        const { fooId } = request.params;
        const bars = await db
          .select()
          .from(bar)
          .where(eq(bar.fooId, fooId))
          .orderBy(desc(bar.createdAt));

        return reply.send(bars);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch bars for foo" });
      }
    }
  );
} 