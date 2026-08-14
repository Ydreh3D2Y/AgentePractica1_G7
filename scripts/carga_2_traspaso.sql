-- Carga manual - PASO 3 de 3: traspaso y verificacion.
-- Requiere haber corrido carga_1_crear_staging.sql y haber importado el CSV
-- a staging_ventas.

SELECT count(*) AS filas_en_staging FROM staging_ventas;
-- Resultado debe ser 6500 filas.


-- Traspaso: cliente primero, porque compra tiene FK hacia cliente.

INSERT INTO cliente (id_cliente, edad, genero, venta_total, n_compras, boletin, vale)
SELECT id_cliente, edad, genero, venta_total, n_compras, boletin, vale
FROM staging_ventas;

INSERT INTO compra (id_cliente, fecha_compra, monto_compra, metodo_pago_id, navegador_id, tiempo_seg)
SELECT id_cliente, fecha_compra, monto_compra, metodo_pago_id, navegador_id, tiempo_seg
FROM staging_ventas;


-- Verificacion. Valores esperados: clientes = 6500, compras = 6500,
-- suma_venta_total = 1340575.80, suma_monto_compra = 258615.861

SELECT count(*) AS clientes FROM cliente;
SELECT count(*) AS compras  FROM compra;
SELECT sum(venta_total)  AS suma_venta_total  FROM cliente;
SELECT sum(monto_compra) AS suma_monto_compra FROM compra;

SELECT mes_nombre, count(*) AS compras, round(sum(monto_compra), 2) AS monto
FROM v_ventas
GROUP BY mes, mes_nombre
ORDER BY mes;


-- Limpieza: ejecutar solo cuando los numeros de arriba ya coincidan.

DROP TABLE staging_ventas;
