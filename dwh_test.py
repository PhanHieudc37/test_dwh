import sqlite3
import time
from datetime import datetime, timedelta
import random
import statistics

class DWHTest:
    def __init__(self, db_name=':memory:'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.test_count = 0
        self.passed_count = 0
    
    def setup_warehouse(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dim_date (
                date_id INTEGER PRIMARY KEY,
                full_date DATE,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                quarter INTEGER
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dim_product (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT,
                category TEXT,
                price REAL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dim_customer (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT,
                region TEXT,
                status TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fact_sales (
                sale_id INTEGER PRIMARY KEY,
                date_id INTEGER,
                product_id INTEGER,
                customer_id INTEGER,
                quantity INTEGER,
                amount REAL,
                FOREIGN KEY(date_id) REFERENCES dim_date(date_id),
                FOREIGN KEY(product_id) REFERENCES dim_product(product_id),
                FOREIGN KEY(customer_id) REFERENCES dim_customer(customer_id)
            )
        ''')
        
        self.conn.commit()
    
    def load_sample_data(self):
        base_date = datetime(2024, 1, 1)
        for i in range(365):
            current_date = base_date + timedelta(days=i)
            self.cursor.execute('''
                INSERT INTO dim_date (date_id, full_date, year, month, day, quarter)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                i + 1,
                current_date.date(),
                current_date.year,
                current_date.month,
                current_date.day,
                (current_date.month - 1) // 3 + 1
            ))
        
        products = [
            ('Laptop', 'Electronics', 1200),
            ('Mouse', 'Electronics', 25),
            ('Keyboard', 'Electronics', 75),
            ('Monitor', 'Electronics', 350),
            ('Desk', 'Furniture', 400),
            ('Chair', 'Furniture', 250),
            ('Lamp', 'Furniture', 50),
            ('Coffee', 'Beverages', 5),
            ('Tea', 'Beverages', 3),
            ('Snacks', 'Beverages', 8)
        ]
        
        for product_id, (name, category, price) in enumerate(products, 1):
            self.cursor.execute('''
                INSERT INTO dim_product (product_id, product_name, category, price)
                VALUES (?, ?, ?, ?)
            ''', (product_id, name, category, price))
        
        regions = ['North', 'South', 'East', 'West', 'Central']
        for customer_id in range(1, 101):
            self.cursor.execute('''
                INSERT INTO dim_customer (customer_id, customer_name, region, status)
                VALUES (?, ?, ?, ?)
            ''', (
                customer_id,
                f'Customer_{customer_id}',
                random.choice(regions),
                'Active' if random.random() > 0.1 else 'Inactive'
            ))
        
        for sale_id in range(1, 5001):
            self.cursor.execute('''
                INSERT INTO fact_sales (date_id, product_id, customer_id, quantity, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                random.randint(1, 365),
                random.randint(1, 10),
                random.randint(1, 100),
                random.randint(1, 10),
                round(random.uniform(10, 5000), 2)
            ))
        
        self.conn.commit()
    
    def test_schema_validation(self):
        print("\n[TEST 1] Schema Validation")
        print("-" * 50)
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()
        table_names = [t[0] for t in tables]
        
        required_tables = ['dim_date', 'dim_product', 'dim_customer', 'fact_sales']
        print(f"Required tables: {required_tables}")
        print(f"Found tables: {table_names}")
        
        self.test_count += 1
        if all(t in table_names for t in required_tables):
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_data_loading(self):
        print("\n[TEST 2] Data Loading")
        print("-" * 50)
        
        self.cursor.execute("SELECT COUNT(*) FROM fact_sales")
        sales_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dim_customer")
        customer_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dim_product")
        product_count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dim_date")
        date_count = self.cursor.fetchone()[0]
        
        print(f"Sales records: {sales_count}")
        print(f"Customers: {customer_count}")
        print(f"Products: {product_count}")
        print(f"Dates: {date_count}")
        
        self.test_count += 1
        if sales_count > 0 and customer_count > 0 and product_count > 0 and date_count > 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_data_quality(self):
        print("\n[TEST 3] Data Quality Check")
        print("-" * 50)
        
        self.cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0")
        invalid_qty = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM fact_sales WHERE amount <= 0")
        invalid_amount = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM dim_product WHERE price <= 0")
        invalid_price = self.cursor.fetchone()[0]
        
        print(f"Invalid quantities: {invalid_qty}")
        print(f"Invalid amounts: {invalid_amount}")
        print(f"Invalid prices: {invalid_price}")
        
        self.test_count += 1
        if invalid_qty == 0 and invalid_amount == 0 and invalid_price == 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_referential_integrity(self):
        print("\n[TEST 4] Referential Integrity")
        print("-" * 50)
        
        self.cursor.execute('''
            SELECT COUNT(*) FROM fact_sales fs
            WHERE NOT EXISTS (SELECT 1 FROM dim_date dd WHERE dd.date_id = fs.date_id)
        ''')
        orphan_dates = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            SELECT COUNT(*) FROM fact_sales fs
            WHERE NOT EXISTS (SELECT 1 FROM dim_product dp WHERE dp.product_id = fs.product_id)
        ''')
        orphan_products = self.cursor.fetchone()[0]
        
        self.cursor.execute('''
            SELECT COUNT(*) FROM fact_sales fs
            WHERE NOT EXISTS (SELECT 1 FROM dim_customer dc WHERE dc.customer_id = fs.customer_id)
        ''')
        orphan_customers = self.cursor.fetchone()[0]
        
        print(f"Orphan date references: {orphan_dates}")
        print(f"Orphan product references: {orphan_products}")
        print(f"Orphan customer references: {orphan_customers}")
        
        self.test_count += 1
        if orphan_dates == 0 and orphan_products == 0 and orphan_customers == 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_aggregate_functions(self):
        print("\n[TEST 5] Aggregate Functions")
        print("-" * 50)
        
        self.cursor.execute("SELECT SUM(amount), AVG(amount), COUNT(*) FROM fact_sales")
        total_sales, avg_sales, count_sales = self.cursor.fetchone()
        
        self.cursor.execute("SELECT SUM(quantity) FROM fact_sales")
        total_qty = self.cursor.fetchone()[0]
        
        print(f"Total sales: ${total_sales:.2f}")
        print(f"Average sale: ${avg_sales:.2f}")
        print(f"Total records: {count_sales}")
        print(f"Total quantity: {total_qty}")
        
        self.test_count += 1
        if total_sales > 0 and avg_sales > 0 and count_sales > 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_dimension_tables(self):
        print("\n[TEST 6] Dimension Tables")
        print("-" * 50)
        
        self.cursor.execute("SELECT COUNT(DISTINCT region) FROM dim_customer")
        regions = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(DISTINCT category) FROM dim_product")
        categories = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(DISTINCT quarter) FROM dim_date")
        quarters = self.cursor.fetchone()[0]
        
        print(f"Unique regions: {regions}")
        print(f"Unique categories: {categories}")
        print(f"Unique quarters: {quarters}")
        
        self.test_count += 1
        if regions > 0 and categories > 0 and quarters > 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_query_performance(self):
        print("\n[TEST 7] Query Performance")
        print("-" * 50)
        
        queries = [
            "SELECT COUNT(*) FROM fact_sales",
            "SELECT SUM(amount) FROM fact_sales WHERE quantity > 5",
            "SELECT dc.region, SUM(fs.amount) FROM fact_sales fs JOIN dim_customer dc ON fs.customer_id = dc.customer_id GROUP BY dc.region",
            "SELECT dp.category, COUNT(*) FROM fact_sales fs JOIN dim_product dp ON fs.product_id = dp.product_id GROUP BY dp.category"
        ]
        
        times = []
        for query in queries:
            start = time.time()
            self.cursor.execute(query)
            self.cursor.fetchall()
            end = time.time()
            elapsed = (end - start) * 1000
            times.append(elapsed)
            print(f"Query execution: {elapsed:.2f} ms")
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"Average time: {avg_time:.2f} ms")
        print(f"Max time: {max_time:.2f} ms")
        
        self.test_count += 1
        if max_time < 1000:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_duplicate_detection(self):
        print("\n[TEST 8] Duplicate Detection")
        print("-" * 50)
        
        self.cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT date_id, product_id, customer_id, COUNT(*) as cnt
                FROM fact_sales
                GROUP BY date_id, product_id, customer_id
                HAVING cnt > 1
            )
        ''')
        duplicates = self.cursor.fetchone()[0]
        
        print(f"Duplicate records: {duplicates}")
        
        self.test_count += 1
        if duplicates == 0:
            self.passed_count += 1
            print("✓ PASSED (No duplicates)")
        else:
            print("⚠ WARNING (Duplicates found)")
    
    def test_business_logic(self):
        print("\n[TEST 9] Business Logic")
        print("-" * 50)
        
        self.cursor.execute('''
            SELECT dc.region, SUM(fs.amount) as total_sales
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_id = dc.customer_id
            GROUP BY dc.region
        ''')
        results = self.cursor.fetchall()
        
        print("Sales by region:")
        for region, total in results:
            print(f"  {region}: ${total:.2f}")
        
        self.test_count += 1
        if len(results) > 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def test_time_series(self):
        print("\n[TEST 10] Time Series Analysis")
        print("-" * 50)
        
        self.cursor.execute('''
            SELECT dd.month, SUM(fs.amount) as monthly_sales, COUNT(*) as transactions
            FROM fact_sales fs
            JOIN dim_date dd ON fs.date_id = dd.date_id
            GROUP BY dd.month
            ORDER BY dd.month
        ''')
        results = self.cursor.fetchall()
        
        print("Sales by month:")
        for month, sales, trans in results:
            print(f"  Month {month}: ${sales:.2f} ({trans} transactions)")
        
        self.test_count += 1
        if len(results) > 0:
            self.passed_count += 1
            print("✓ PASSED")
        else:
            print("✗ FAILED")
    
    def run_all_tests(self):
        print("=" * 60)
        print("DATA WAREHOUSE TEST SUITE")
        print("=" * 60)
        
        self.setup_warehouse()
        self.load_sample_data()
        
        self.test_schema_validation()
        self.test_data_loading()
        self.test_data_quality()
        self.test_referential_integrity()
        self.test_aggregate_functions()
        self.test_dimension_tables()
        self.test_query_performance()
        self.test_duplicate_detection()
        self.test_business_logic()
        self.test_time_series()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.test_count - self.passed_count}")
        print(f"Pass Rate: {(self.passed_count / self.test_count * 100):.1f}%")
        print("=" * 60)
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    dwh_test = DWHTest()
    dwh_test.run_all_tests()
    dwh_test.close()
    print("\n✓ DWH testing completed!")
