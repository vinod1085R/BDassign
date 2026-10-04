const express = require("express");
const sqlite3 = require("sqlite3").verbose();

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());

// Connect to SQLite database
const db = new sqlite3.Database("sunshine.db", (err) => {
    if (err) {
        console.log("Database connection failed:", err.message);
        return;
    }

    console.log("SQLite database connected successfully");
});

// Create Products table
db.run(`
    CREATE TABLE IF NOT EXISTS products (
        p_id INTEGER PRIMARY KEY AUTOINCREMENT,
        p_type TEXT NOT NULL,
        p_name TEXT NOT NULL,
        price INTEGER NOT NULL,
        p_color TEXT NOT NULL
    )
`, (err) => {
    if (err) {
        console.log("Table creation failed:", err.message);
    } else {
        console.log("Products table ready");
    }
});


// GET - All products
app.get("/products", (req, res) => {

    const sql = "SELECT * FROM products";

    db.all(sql, [], (err, rows) => {

        if (err) {
            return res.status(500).json({
                error: err.message
            });
        }

        res.json(rows);
    });
});


// GET - One product
app.get("/products/:id", (req, res) => {

    const id = req.params.id;

    const sql = "SELECT * FROM products WHERE p_id = ?";

    db.get(sql, [id], (err, row) => {

        if (err) {
            return res.status(500).json({
                error: err.message
            });
        }

        if (!row) {
            return res.status(404).json({
                message: "Product not found"
            });
        }

        res.json(row);
    });
});


// POST - Add product
app.post("/products", (req, res) => {

    const { p_type, p_name, price, p_color } = req.body;

    const sql = `
        INSERT INTO products (p_type, p_name, price, p_color)
        VALUES (?, ?, ?, ?)
    `;

    db.run(
        sql,
        [p_type, p_name, price, p_color],
        function (err) {

            if (err) {
                return res.status(500).json({
                    error: err.message
                });
            }

            res.status(201).json({
                message: "Product added successfully",
                id: this.lastID
            });
        }
    );
});


// PUT - Update product
app.put("/products/:id", (req, res) => {

    const id = req.params.id;

    const { p_type, p_name, price, p_color } = req.body;

    const sql = `
        UPDATE products
        SET p_type = ?, p_name = ?, price = ?, p_color = ?
        WHERE p_id = ?
    `;

    db.run(
        sql,
        [p_type, p_name, price, p_color, id],
        function (err) {

            if (err) {
                return res.status(500).json({
                    error: err.message
                });
            }

            if (this.changes === 0) {
                return res.status(404).json({
                    message: "Product not found"
                });
            }

            res.json({
                message: "Product updated successfully"
            });
        }
    );
});


// DELETE - Delete product
app.delete("/products/:id", (req, res) => {

    const id = req.params.id;

    const sql = "DELETE FROM products WHERE p_id = ?";

    db.run(sql, [id], function (err) {

        if (err) {
            return res.status(500).json({
                error: err.message
            });
        }

        if (this.changes === 0) {
            return res.status(404).json({
                message: "Product not found"
            });
        }

        res.json({
            message: "Product deleted successfully"
        });
    });
});


// Start server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});