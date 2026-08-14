-- Modelo relacional para el analisis de ventas online 2021.
-- Motor: PostgreSQL 15+ (Supabase). Ejecucion: SQL Editor -> pegar -> Run.
-- Idempotente: puede ejecutarse varias veces sin error.

DROP VIEW  IF EXISTS v_ventas       CASCADE;
DROP TABLE IF EXISTS compra         CASCADE;
DROP TABLE IF EXISTS cliente        CASCADE;
DROP TABLE IF EXISTS metodo_pago    CASCADE;
DROP TABLE IF EXISTS navegador      CASCADE;


-- 1. Catalogos: traducen los codigos del CSV a etiquetas legibles.

CREATE TABLE metodo_pago (
    metodo_pago_id  SMALLINT     PRIMARY KEY,
    nombre          VARCHAR(30)  NOT NULL UNIQUE,
    es_efectivo     BOOLEAN      NOT NULL
);

COMMENT ON TABLE  metodo_pago IS
    'Catalogo de metodos de pago segun la seccion 3.1 del enunciado.';
COMMENT ON COLUMN metodo_pago.es_efectivo IS
    'TRUE unicamente para Efectivo.';


CREATE TABLE navegador (
    navegador_id    SMALLINT     PRIMARY KEY,
    nombre          VARCHAR(30)  NOT NULL UNIQUE,
    -- Codigo 0 = Tienda Fisica, no es un navegador web.
    es_online       BOOLEAN      NOT NULL
);

COMMENT ON TABLE  navegador IS
    'Catalogo de canales de venta. El codigo 0 corresponde a Tienda Fisica.';
COMMENT ON COLUMN navegador.es_online IS
    'FALSE para Tienda Fisica, TRUE para los navegadores web.';


-- 2. Cliente: atributos constantes del ano (demograficos, totales, flags).

CREATE TABLE cliente (
    id_cliente      BIGINT        PRIMARY KEY,
    edad            SMALLINT      NOT NULL,
    genero          SMALLINT      NOT NULL,
    venta_total     NUMERIC(12,2) NOT NULL,
    n_compras       SMALLINT      NOT NULL,
    boletin         SMALLINT      NOT NULL,
    vale            SMALLINT      NOT NULL,

    CONSTRAINT ck_cliente_edad        CHECK (edad BETWEEN 18 AND 100),
    CONSTRAINT ck_cliente_genero      CHECK (genero IN (0, 1)),
    CONSTRAINT ck_cliente_venta       CHECK (venta_total > 0),
    CONSTRAINT ck_cliente_n_compras   CHECK (n_compras >= 1),
    CONSTRAINT ck_cliente_boletin     CHECK (boletin IN (0, 1)),
    CONSTRAINT ck_cliente_vale        CHECK (vale IN (0, 1))
);

COMMENT ON TABLE  cliente IS
    'Un registro por cliente con sus totales acumulados del ano 2021.';
COMMENT ON COLUMN cliente.genero IS
    '0 = Masculino, 1 = Femenino.';
COMMENT ON COLUMN cliente.venta_total IS
    'Monto total acumulado por el cliente durante el ano.';
COMMENT ON COLUMN cliente.n_compras IS
    'Cantidad de compras realizadas por el cliente durante el ano.';
COMMENT ON COLUMN cliente.boletin IS
    '1 = suscrito al boletin, 0 = no suscrito.';
COMMENT ON COLUMN cliente.vale IS
    '1 = utilizo vale de descuento, 0 = no utilizo.';


-- 3. Compra: atributos que varian por transaccion.
-- monto_compra no equivale a venta_total / n_compras (solo coincide en 7 de
-- 6,500 filas), por eso es una entidad aparte y no un campo derivado.
-- Relacion 1:N con cliente, aunque hoy haya una compra por cliente.

CREATE TABLE compra (
    compra_id       BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente      BIGINT        NOT NULL,
    fecha_compra    DATE          NOT NULL,
    monto_compra    NUMERIC(12,3) NOT NULL,
    metodo_pago_id  SMALLINT      NOT NULL,
    navegador_id    SMALLINT      NOT NULL,
    tiempo_seg      SMALLINT      NOT NULL,

    CONSTRAINT fk_compra_cliente
        FOREIGN KEY (id_cliente)     REFERENCES cliente (id_cliente)
        ON DELETE CASCADE,
    CONSTRAINT fk_compra_metodo_pago
        FOREIGN KEY (metodo_pago_id) REFERENCES metodo_pago (metodo_pago_id),
    CONSTRAINT fk_compra_navegador
        FOREIGN KEY (navegador_id)   REFERENCES navegador (navegador_id),

    CONSTRAINT ck_compra_monto  CHECK (monto_compra > 0),
    CONSTRAINT ck_compra_tiempo CHECK (tiempo_seg > 0),
    CONSTRAINT ck_compra_fecha
        CHECK (fecha_compra BETWEEN DATE '2021-01-01' AND DATE '2021-12-31')
);

COMMENT ON TABLE  compra IS
    'Transaccion registrada de un cliente. Relacion 1:N con cliente.';
COMMENT ON COLUMN compra.monto_compra IS
    'Monto de la transaccion. NUMERIC(12,3): el origen trae 3 decimales.';
COMMENT ON COLUMN compra.tiempo_seg IS
    'Duracion de la sesion en segundos (rango observado 180-1443).';


-- 4. Indices sobre las columnas de filtro y agrupacion mas frecuentes.

CREATE INDEX ix_compra_fecha       ON compra (fecha_compra);
CREATE INDEX ix_compra_metodo_pago ON compra (metodo_pago_id);
CREATE INDEX ix_compra_navegador   ON compra (navegador_id);
CREATE INDEX ix_compra_cliente     ON compra (id_cliente);
CREATE INDEX ix_cliente_edad       ON cliente (edad);


-- 5. Carga de catalogos.

INSERT INTO metodo_pago (metodo_pago_id, nombre, es_efectivo) VALUES
    (0, 'Efectivo',           TRUE),
    (1, 'Tarjeta de Credito', FALSE),
    (2, 'Tarjeta de Debito',  FALSE);

INSERT INTO navegador (navegador_id, nombre, es_online) VALUES
    (0, 'Tienda Fisica', FALSE),
    (1, 'Navegador 1',   TRUE),
    (2, 'Navegador 2',   TRUE),
    (3, 'Navegador 3',   TRUE),
    (4, 'Navegador 4',   TRUE);


-- 6. Vista de analisis: une las cuatro tablas con etiquetas legibles y
-- columnas de mes derivadas. Punto de entrada unico para el analisis.

CREATE VIEW v_ventas AS
SELECT
    c.id_cliente,
    c.edad,
    c.genero,
    CASE c.genero WHEN 1 THEN 'Femenino' ELSE 'Masculino' END AS genero_desc,
    c.venta_total,
    c.n_compras,
    c.boletin,
    CASE c.boletin WHEN 1 THEN 'Si' ELSE 'No' END             AS boletin_desc,
    c.vale,
    CASE c.vale    WHEN 1 THEN 'Si' ELSE 'No' END             AS vale_desc,

    co.compra_id,
    co.fecha_compra,
    EXTRACT(MONTH FROM co.fecha_compra)::SMALLINT             AS mes,
    -- Nombres de mes explicitos: TO_CHAR depende del locale del servidor
    -- y en Supabase devuelve los meses en ingles.
    CASE EXTRACT(MONTH FROM co.fecha_compra)
        WHEN  1 THEN 'Enero'      WHEN  2 THEN 'Febrero'
        WHEN  3 THEN 'Marzo'      WHEN  4 THEN 'Abril'
        WHEN  5 THEN 'Mayo'       WHEN  6 THEN 'Junio'
        WHEN  7 THEN 'Julio'      WHEN  8 THEN 'Agosto'
        WHEN  9 THEN 'Septiembre' WHEN 10 THEN 'Octubre'
        WHEN 11 THEN 'Noviembre'  WHEN 12 THEN 'Diciembre'
    END                                                       AS mes_nombre,
    TO_CHAR(co.fecha_compra, 'YYYY-MM')                       AS anio_mes,
    co.monto_compra,
    co.tiempo_seg,

    mp.metodo_pago_id,
    mp.nombre       AS metodo_pago_desc,
    mp.es_efectivo,

    nv.navegador_id,
    nv.nombre       AS navegador_desc,
    nv.es_online
FROM compra co
JOIN cliente     c  ON c.id_cliente      = co.id_cliente
JOIN metodo_pago mp ON mp.metodo_pago_id = co.metodo_pago_id
JOIN navegador   nv ON nv.navegador_id   = co.navegador_id;

COMMENT ON VIEW v_ventas IS
    'Vista desnormalizada con etiquetas legibles y columnas de mes.';
