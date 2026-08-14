-- Carga manual - PASO 1 de 3: crear la tabla puente.
-- Luego: PASO 2 (importar CSV de ventas_limpias a la tabla puente) y pasar al carga_2_traspaso.sql.

DROP TABLE IF EXISTS staging_ventas;

CREATE TABLE staging_ventas (
    id_cliente      BIGINT,
    edad            SMALLINT,
    genero          SMALLINT,
    venta_total     NUMERIC(12,2),
    n_compras       SMALLINT,
    fecha_compra    DATE,
    monto_compra    NUMERIC(12,3),
    metodo_pago_id  SMALLINT,
    tiempo_seg      SMALLINT,
    navegador_id    SMALLINT,
    boletin         SMALLINT,
    vale            SMALLINT
);
