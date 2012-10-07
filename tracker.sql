DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS hosts;


CREATE TABLE customers(
    id integer primary key autoincrement,
    created_at date not null,
    updated_at date not null,
    account_name string not null,
    account_number integer not null,
    controller_id integer not null,
    controller_ip string not null,
    admin_user string not null,
    admin_pass string not null,
    notes string,
    deleted integer not null
);

CREATE INDEX account ON customers (id, account_name, account_number);


-- CREATE TABLE hosts(
--     id integer primary key autoincrement,
--     customer_id integer,
--     host_name string not null,
--     host_number integer,
--     host_ip string not null,
--     type string not null
-- );

-- CREATE INDEX customer ON hosts (id, customer_id);
-- CREATE INDEX host ON hosts (host_name, host_number, host_ip);
