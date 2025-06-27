import { db, pool } from "../database/connection";
import { users, products, orders, orderItems } from "../database/schema";

async function seedDatabase() {
  console.log("🌱 Seeding database with sample data...");

  try {
    // Clean existing data
    console.log("Cleaning existing data...");
    await db.delete(orderItems);
    await db.delete(orders);
    await db.delete(products);
    await db.delete(users);

    // Create sample users
    console.log("Creating sample users...");
    const sampleUsers = await db
      .insert(users)
      .values([
        {
          email: "john.doe@example.com",
          firstName: "John",
          lastName: "Doe",
        },
        {
          email: "jane.smith@example.com",
          firstName: "Jane",
          lastName: "Smith",
        },
        {
          email: "bob.wilson@example.com",
          firstName: "Bob",
          lastName: "Wilson",
        },
      ])
      .returning();

    console.log(`✅ Created ${sampleUsers.length} users`);

    // Create sample products
    console.log("Creating sample products...");
    const sampleProducts = await db
      .insert(products)
      .values([
        {
          name: 'MacBook Pro 16"',
          description: "Apple MacBook Pro 16-inch with M3 Pro chip",
          price: 249900, // $2,499.00
          isAvailable: true,
        },
        {
          name: "iPhone 15 Pro",
          description: "Apple iPhone 15 Pro with A17 Pro chip",
          price: 99900, // $999.00
          isAvailable: true,
        },
        {
          name: "AirPods Pro",
          description: "Apple AirPods Pro (2nd generation)",
          price: 24900, // $249.00
          isAvailable: true,
        },
        {
          name: "iPad Air",
          description: "Apple iPad Air with M1 chip",
          price: 59900, // $599.00
          isAvailable: true,
        },
        {
          name: "Apple Watch Series 9",
          description: "Apple Watch Series 9 GPS + Cellular",
          price: 42900, // $429.00
          isAvailable: true,
        },
        {
          name: "Magic Keyboard",
          description: "Apple Magic Keyboard with Touch ID",
          price: 19900, // $199.00
          isAvailable: false, // Out of stock
        },
      ])
      .returning();

    console.log(`✅ Created ${sampleProducts.length} products`);

    // Create sample orders
    console.log("Creating sample orders...");

    // Order 1: John buys MacBook and AirPods
    const order1 = await db
      .insert(orders)
      .values({
        userId: sampleUsers[0].id,
        status: "pending",
        totalAmount: 274800, // MacBook + AirPods
      })
      .returning();

    await db.insert(orderItems).values([
      {
        orderId: order1[0].id,
        productId: sampleProducts[0].id, // MacBook Pro
        quantity: 1,
        pricePerItem: 249900,
      },
      {
        orderId: order1[0].id,
        productId: sampleProducts[2].id, // AirPods Pro
        quantity: 1,
        pricePerItem: 24900,
      },
    ]);

    // Order 2: Jane buys iPhone and Apple Watch
    const order2 = await db
      .insert(orders)
      .values({
        userId: sampleUsers[1].id,
        status: "confirmed",
        totalAmount: 142800, // iPhone + Apple Watch
      })
      .returning();

    await db.insert(orderItems).values([
      {
        orderId: order2[0].id,
        productId: sampleProducts[1].id, // iPhone 15 Pro
        quantity: 1,
        pricePerItem: 99900,
      },
      {
        orderId: order2[0].id,
        productId: sampleProducts[4].id, // Apple Watch
        quantity: 1,
        pricePerItem: 42900,
      },
    ]);

    // Order 3: Bob buys iPad and multiple AirPods
    const order3 = await db
      .insert(orders)
      .values({
        userId: sampleUsers[2].id,
        status: "delivered",
        totalAmount: 109700, // iPad + 2x AirPods
      })
      .returning();

    await db.insert(orderItems).values([
      {
        orderId: order3[0].id,
        productId: sampleProducts[3].id, // iPad Air
        quantity: 1,
        pricePerItem: 59900,
      },
      {
        orderId: order3[0].id,
        productId: sampleProducts[2].id, // AirPods Pro
        quantity: 2,
        pricePerItem: 24900,
      },
    ]);

    console.log("✅ Created 3 sample orders with order items");

    console.log("🎉 Database seeded successfully!");
    console.log("");
    console.log("Sample data created:");
    console.log(`- ${sampleUsers.length} users`);
    console.log(`- ${sampleProducts.length} products`);
    console.log("- 3 orders with multiple items");
    console.log("");
    console.log("You can now test the API endpoints:");
    console.log("- GET http://localhost:8080/api/users");
    console.log("- GET http://localhost:8080/api/products");
    console.log("- GET http://localhost:8080/api/orders");
  } catch (error) {
    console.error("❌ Seeding failed:", error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  seedDatabase();
}

export { seedDatabase };
