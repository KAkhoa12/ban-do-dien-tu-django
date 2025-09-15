-- TABLE
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);
CREATE TABLE "frontend_brand" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(255) NOT NULL, "image_url" text NOT NULL, "slug" text NOT NULL, "created_at" datetime NOT NULL);
CREATE TABLE "frontend_cart" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "created_at" datetime NOT NULL, "user_id" bigint NOT NULL REFERENCES "frontend_user" ("id") DEFERRABLE INITIALLY DEFERRED, "status" varchar(10) NOT NULL);
CREATE TABLE "frontend_cartdetail" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "product_options" text NOT NULL, "quantity" integer NOT NULL, "cart_id" bigint NOT NULL REFERENCES "frontend_cart" ("id") DEFERRABLE INITIALLY DEFERRED, "product_id" bigint NOT NULL REFERENCES "frontend_product" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "frontend_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(255) NOT NULL, "image_url" text NOT NULL, "slug" text NOT NULL, "description" text NULL, "created_at" datetime NOT NULL);
CREATE TABLE "frontend_congtrinhtoandien" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(255) NOT NULL, "created_at" datetime NOT NULL, "content" text NOT NULL, "author_id" bigint NOT NULL REFERENCES "frontend_user" ("id") DEFERRABLE INITIALLY DEFERRED, "status" varchar(20) NOT NULL, "description" text NOT NULL, "image_url" text NOT NULL);
CREATE TABLE "frontend_giaiphapamthanh" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(255) NOT NULL, "created_at" datetime NOT NULL, "content" text NOT NULL, "youtube_url" varchar(200) NULL, "author_id" bigint NOT NULL REFERENCES "frontend_user" ("id") DEFERRABLE INITIALLY DEFERRED, "status" varchar(20) NOT NULL, "description" text NOT NULL, "image_url" text NOT NULL);
CREATE TABLE "frontend_momopayment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "order_id" varchar(50) NOT NULL UNIQUE, "amount" decimal NOT NULL, "order_info" varchar(255) NOT NULL, "request_id" varchar(50) NOT NULL UNIQUE, "transaction_id" varchar(50) NULL, "message" varchar(255) NULL, "response_time" datetime NULL, "status" varchar(20) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);
CREATE TABLE "frontend_order" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "total_price" real NOT NULL, "created_at" datetime NOT NULL, "user_id" bigint NOT NULL REFERENCES "frontend_user" ("id") DEFERRABLE INITIALLY DEFERRED, "status" varchar(10) NOT NULL);
CREATE TABLE "frontend_orderdetail" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "product_options" text NOT NULL, "quantity" integer NOT NULL, "price" real NOT NULL, "order_id" bigint NOT NULL REFERENCES "frontend_order" ("id") DEFERRABLE INITIALLY DEFERRED, "product_id" bigint NOT NULL REFERENCES "frontend_product" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "frontend_product" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(255) NOT NULL, "description" text NULL, "price" real NOT NULL, "old_price" real NULL, "tags" text NULL, "stock" integer NOT NULL, "created_at" datetime NOT NULL, "number_of_sell" integer NOT NULL, "image_url" text NOT NULL, "number_of_like" integer NOT NULL, "brand_id" bigint NULL REFERENCES "frontend_brand" ("id") DEFERRABLE INITIALLY DEFERRED, "category_id" bigint NOT NULL REFERENCES "frontend_category" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "frontend_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(255) NOT NULL, "email" varchar(254) NOT NULL UNIQUE, "phone" varchar(15) NOT NULL, "address" text NOT NULL, "image_url" text NOT NULL, "password" varchar(255) NOT NULL, "username" varchar(255) NOT NULL UNIQUE, "role" varchar(10) NOT NULL, "created_at" datetime NOT NULL);
 
-- INDEX
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");
CREATE INDEX "frontend_cart_user_id_2778fd0a" ON "frontend_cart" ("user_id");
CREATE INDEX "frontend_cartdetail_cart_id_cdc0b470" ON "frontend_cartdetail" ("cart_id");
CREATE INDEX "frontend_cartdetail_product_id_7d23f9e6" ON "frontend_cartdetail" ("product_id");
CREATE INDEX "frontend_congtrinhtoandien_author_id_b912c2fd" ON "frontend_congtrinhtoandien" ("author_id");
CREATE INDEX "frontend_giaiphapamthanh_author_id_1ca27849" ON "frontend_giaiphapamthanh" ("author_id");
CREATE INDEX "frontend_order_user_id_d6d9e577" ON "frontend_order" ("user_id");
CREATE INDEX "frontend_orderdetail_order_id_c0e23c34" ON "frontend_orderdetail" ("order_id");
CREATE INDEX "frontend_orderdetail_product_id_14d6f794" ON "frontend_orderdetail" ("product_id");
CREATE INDEX "frontend_product_brand_id_ce4305a0" ON "frontend_product" ("brand_id");
CREATE INDEX "frontend_product_category_id_62b1b6df" ON "frontend_product" ("category_id");
 
-- TRIGGER
 
-- VIEW
 
