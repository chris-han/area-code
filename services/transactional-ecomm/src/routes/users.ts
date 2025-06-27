import { FastifyInstance } from "fastify";
import { eq } from "drizzle-orm";
import { db } from "../database/connection";
import {
  users,
  insertUserSchema,
  selectUserSchema,
  type User,
  type NewUser,
} from "../database/schema";

export async function userRoutes(fastify: FastifyInstance) {
  // Get all users
  fastify.get<{ Reply: User[] | { error: string } }>(
    "/users",
    async (request, reply) => {
      try {
        const allUsers = await db.select().from(users);
        return reply.send(allUsers);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch users" });
      }
    }
  );

  // Get user by ID
  fastify.get<{ Params: { id: string }; Reply: User | { error: string } }>(
    "/users/:id",
    async (request, reply) => {
      try {
        const { id } = request.params;
        const user = await db
          .select()
          .from(users)
          .where(eq(users.id, id))
          .limit(1);

        if (user.length === 0) {
          return reply.status(404).send({ error: "User not found" });
        }

        return reply.send(user[0]);
      } catch (error) {
        return reply.status(500).send({ error: "Failed to fetch user" });
      }
    }
  );

  // Create new user
  fastify.post<{ Body: NewUser; Reply: User | { error: string } }>(
    "/users",
    async (request, reply) => {
      try {
        const validatedData = insertUserSchema.parse(request.body);
        const newUser = await db
          .insert(users)
          .values(validatedData)
          .returning();

        return reply.status(201).send(newUser[0]);
      } catch (error) {
        return reply.status(400).send({ error: "Invalid user data" });
      }
    }
  );

  // Update user
  fastify.put<{
    Params: { id: string };
    Body: Partial<NewUser>;
    Reply: User | { error: string };
  }>("/users/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const updateData = { ...request.body, updatedAt: new Date() };

      const updatedUser = await db
        .update(users)
        .set(updateData)
        .where(eq(users.id, id))
        .returning();

      if (updatedUser.length === 0) {
        return reply.status(404).send({ error: "User not found" });
      }

      return reply.send(updatedUser[0]);
    } catch (error) {
      return reply.status(400).send({ error: "Failed to update user" });
    }
  });

  // Delete user
  fastify.delete<{
    Params: { id: string };
    Reply: { success: boolean } | { error: string };
  }>("/users/:id", async (request, reply) => {
    try {
      const { id } = request.params;
      const deletedUser = await db
        .delete(users)
        .where(eq(users.id, id))
        .returning();

      if (deletedUser.length === 0) {
        return reply.status(404).send({ error: "User not found" });
      }

      return reply.send({ success: true });
    } catch (error) {
      return reply.status(500).send({ error: "Failed to delete user" });
    }
  });
}
