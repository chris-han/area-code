import { db, pool } from "../database/connection";
import { foo, bar, fooBar } from "../database/schema";

async function seedDatabase() {
  console.log("🌱 Seeding database with sample data...");

  try {
    // Clean existing data
    console.log("Cleaning existing data...");
    await db.delete(fooBar);
    await db.delete(bar);
    await db.delete(foo);

    // Create sample foo items
    console.log("Creating sample foo items...");
    const sampleFoos = await db
      .insert(foo)
      .values([
        {
          name: "Alpha Foo",
          description: "First sample foo entity",
          status: "active",
          priority: 1,
        },
        {
          name: "Beta Foo",
          description: "Second sample foo entity",
          status: "pending",
          priority: 2,
        },
        {
          name: "Gamma Foo",
          description: "Third sample foo entity",
          status: "inactive",
          priority: 3,
          isActive: false,
        },
        {
          name: "Delta Foo",
          description: "Fourth sample foo entity",
          status: "active",
          priority: 1,
        },
      ])
      .returning();

    console.log(`✅ Created ${sampleFoos.length} foo items`);

    // Create sample bar items
    console.log("Creating sample bar items...");
    const sampleBars = await db
      .insert(bar)
      .values([
        {
          fooId: sampleFoos[0].id,
          value: 100,
          label: "First Bar",
          notes: "Associated with Alpha Foo",
        },
        {
          fooId: sampleFoos[0].id,
          value: 200,
          label: "Second Bar",
          notes: "Also associated with Alpha Foo",
        },
        {
          fooId: sampleFoos[1].id,
          value: 150,
          label: "Third Bar",
          notes: "Associated with Beta Foo",
        },
        {
          fooId: sampleFoos[1].id,
          value: 300,
          label: "Fourth Bar",
          notes: "Another bar for Beta Foo",
          isEnabled: false,
        },
        {
          fooId: sampleFoos[3].id,
          value: 250,
          label: "Fifth Bar",
          notes: "Associated with Delta Foo",
        },
      ])
      .returning();

    console.log(`✅ Created ${sampleBars.length} bar items`);

    // Create sample foo-bar relationships (many-to-many)
    console.log("Creating sample foo-bar relationships...");
    await db.insert(fooBar).values([
      {
        fooId: sampleFoos[0].id,
        barId: sampleBars[2].id, // Alpha Foo -> Third Bar (cross-reference)
        relationshipType: "cross-link",
        metadata: JSON.stringify({ strength: "weak", created_by: "system" }),
      },
      {
        fooId: sampleFoos[1].id,
        barId: sampleBars[0].id, // Beta Foo -> First Bar (cross-reference)
        relationshipType: "cross-link",
        metadata: JSON.stringify({ strength: "strong", created_by: "admin" }),
      },
      {
        fooId: sampleFoos[3].id,
        barId: sampleBars[1].id, // Delta Foo -> Second Bar
        relationshipType: "special",
        metadata: JSON.stringify({ strength: "medium", created_by: "user" }),
      },
    ]);

    console.log("✅ Created 3 sample foo-bar relationships");

    console.log("🎉 Database seeded successfully!");
    console.log("");
    console.log("Sample data created:");
    console.log(`- ${sampleFoos.length} foo items`);
    console.log(`- ${sampleBars.length} bar items`);
    console.log("- 3 foo-bar relationships");
    console.log("");
    console.log("You can now test the API endpoints:");
    console.log("- GET http://localhost:8081/api/foo");
    console.log("- GET http://localhost:8081/api/bar");
    console.log("- GET http://localhost:8081/api/foo-bar");
    console.log("- GET http://localhost:8081/api/foo/:id/bars");
    console.log("- GET http://localhost:8081/api/foo/:id/relationships");
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