if opciones_disponibles is not None and len(opciones_disponibles) > 0:
                st.session_state['opciones_disponibles'] = opciones_disponibles
                st.session_state['config_matching'] = config_matching  # Guardar config
                st.success(f"✅ {len(opciones_disponibles)} opciones encontradas con algoritmo mejorado")
                
                # Mostrar estadísticas de matching
                mostrar_estadisticas_matching(opciones_disponibles)
                
                # Mostrar interfaz de selección
                mostrar_interfaz_seleccion_manual(opciones_disponibles, distribucion)
            else:
                st.error("❌ No se encontraron opciones compatibles")
                mostrar_debugging_opciones_mejorado(distribucion, df_proveedor, config_matching)
    
    # Si ya hay opciones disponibles, mostrar la interfaz
    if 'opciones_disponibles' in st.session_state:
        opciones = st.session_state['opciones_disponibles']
        mostrar_interfaz_seleccion_manual(opciones, distribucion)

def mostrar_estadisticas_matching(opciones_disponibles):
    """Muestra estadísticas del matching realizado"""
    st.subheader("📊 Estadísticas del Matching")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_opciones = len(opciones_disponibles)
        st.metric("Opciones Encontradas", f"{total_opciones:,}")
    
    with col2:
        demandas_cubiertas = opciones_disponibles['demanda_id'].nunique()
        total_demandas = len(st.session_state.get('distribucion_demanda', []))
        st.metric("Demandas Cubiertas", f"{demandas_cubiertas}/{total_demandas}")
    
    with col3:
        score_promedio = opciones_disponibles['score_similitud'].mean()
        st.metric("Score Promedio", f"{score_promedio:.1f}")
    
    with col4:
        matches_altos = len(opciones_disponibles[opciones_disponibles['score_similitud'] >= 85])
        st.metric("Matches de Alta Calidad", f"{matches_altos}")
    
    # Distribución de tipos de match
    if len(opciones_disponibles) > 0:
        tipo_dist = opciones_disponibles['tipo_match'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribución por Tipo de Match:**")
            for tipo, cantidad in tipo_dist.items():
                porcentaje = (cantidad / len(opciones_disponibles)) * 100
                st.write(f"• {tipo}: {cantidad} ({porcentaje:.1f}%)")
        
        with col2:
            fig_tipos = px.pie(
                values=tipo_dist.values,
                names=tipo_dist.index,
                title="Distribución de Tipos de Match"
            )
            st.plotly_chart(fig_tipos, use_container_width=True)

# =====================================================
# FUNCIONES DE MATCHING MEJORADAS
# =====================================================

def limpiar_codigo_color_mejorado(color, limpiar_activo=True):
    """Limpia códigos de color removiendo comas y caracteres especiales"""
    if pd.isna(color):
        return ""
    
    color_str = str(color).strip().upper()
    
    if limpiar_activo:
        # Remover comas, puntos, espacios y otros caracteres especiales
        color_limpio = color_str.replace(',', '').replace('.', '').replace(' ', '')
        color_limpio = color_limpio.replace('-', '').replace('_', '').replace('/', '')
        return color_limpio
    else:
        return color_str

def limpiar_sku_mejorado(sku, limpiar_activo=True):
    """Limpia SKUs removiendo comas y caracteres especiales"""
    if pd.isna(sku):
        return ""
    
    sku_str = str(sku).strip().upper()
    
    if limpiar_activo:
        # Remover comas, espacios extra, pero mantener guiones y barras bajas que pueden ser importantes
        sku_limpio = sku_str.replace(',', '').replace(' ', '')
        return sku_limpio
    else:
        return sku_str

def son_colores_iguales_mejorado(color1, color2, limpiar_activo=True):
    """Evalúa si dos colores son exactamente iguales - CON LIMPIEZA DE COMAS"""
    try:
        c1 = limpiar_codigo_color_mejorado(color1, limpiar_activo)
        c2 = limpiar_codigo_color_mejorado(color2, limpiar_activo)
        
        # Comparación exacta después de limpiar
        if c1 == c2:
            return True
        
        # Comparación numérica (para casos como 1001 vs 1,001 vs 1.001)
        try:
            # Intentar convertir a números para comparar
            n1 = float(''.join(filter(str.isdigit, c1)))
            n2 = float(''.join(filter(str.isdigit, c2)))
            return n1 == n2
        except:
            pass
        
        return False
    except:
        return False

def son_colores_similares_mejorado(color1, color2, limpiar_activo=True):
    """Evalúa si dos colores son similares - CON LIMPIEZA DE COMAS"""
    try:
        c1 = limpiar_codigo_color_mejorado(color1, limpiar_activo)
        c2 = limpiar_codigo_color_mejorado(color2, limpiar_activo)
        
        if c1 == c2:
            return True
        
        # Grupos de colores similares (para códigos de texto)
        grupos_colores = [
            ['BLACK', 'NEGRO', 'DARK', 'BLK', 'NOIR'],
            ['WHITE', 'BLANCO', 'CREAM', 'WHT', 'BLANC'],
            ['RED', 'ROJO', 'CRIMSON', 'RD', 'ROUGE'],
            ['BLUE', 'AZUL', 'NAVY', 'BLU', 'BLEU'],
            ['GREEN', 'VERDE', 'GRN', 'VERT'],
            ['BROWN', 'MARRON', 'CAFE', 'BRN', 'BRUN'],
            ['GRAY', 'GREY', 'GRIS', 'GRY']
        ]
        
        for grupo in grupos_colores:
            if c1 in grupo and c2 in grupo:
                return True
        
        # Similitud numérica para códigos cercanos (ej: 1001 vs 1002)
        try:
            n1 = float(''.join(filter(str.isdigit, c1)))
            n2 = float(''.join(filter(str.isdigit, c2)))
            # Considerar similares si difieren en menos de 50
            return abs(n1 - n2) <= 50
        except:
            pass
        
        # Similitud de texto
        return SequenceMatcher(None, c1, c2).ratio() > 0.8
    except:
        return False

def son_tallas_iguales(talla1, talla2):
    """Evalúa si dos tallas son exactamente iguales"""
    try:
        t1 = str(talla1).upper().strip()
        t2 = str(talla2).upper().strip()
        return t1 == t2
    except:
        return False

def son_tallas_similares(talla1, talla2):
    """Evalúa si dos tallas son similares"""
    try:
        grupos_tallas = [
            ['XS', 'XXS', '32', '2'],
            ['S', 'SMALL', '34', '4'],
            ['M', 'MEDIUM', '36', '6'],
            ['L', 'LARGE', '38', '8'],
            ['XL', 'XLARGE', '42', '10']
        ]
        
        t1 = str(talla1).upper().strip()
        t2 = str(talla2).upper().strip()
        
        for grupo in grupos_tallas:
            if t1 in grupo and t2 in grupo:
                return True
        
        # Similitud numérica
        try:
            n1 = float(t1)
            n2 = float(t2)
            return abs(n1 - n2) <= 1
        except:
            pass
        
        return False
    except:
        return False

def normalizar_talla(talla):
    """Convierte tallas numéricas a su equivalente alfabético.

    Por ejemplo, ``"23"`` se transforma en ``"XXS"`` y ``"28"`` en ``"M"``.
    Si la talla ya está en formato de letras, se devuelve sin cambios."""
    if pd.isna(talla):
        return None

    t = str(talla).strip().upper()

    # Si ya es una talla alfabética conocida, retornar tal cual
    if t in [
        "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"
    ]:
        return t

    try:
        n = int(float(t))
    except Exception:
        return t

    if n <= 23:
        return "XXS"
    elif n <= 25:
        return "XS"
    elif n <= 27:
        return "S"
    elif n <= 29:
        return "M"
    elif n <= 31:
        return "L"
    elif n <= 33:
        return "XL"
    elif n <= 35:
        return "XXL"
    else:
        return "XXXL"

def calcular_score_similitud_mejorado_final(demanda, producto, config):
    """Version FINAL del algoritmo de similitud - Soluciona problemas de comas y tallas"""
    score = 0
    
    # 1. Similitud por categoría (50% del score)
    if 'Categoria' in producto and pd.notna(producto['Categoria']):
        if producto['Categoria'].upper().strip() == demanda['categoria'].upper().strip():
            score += 50
        elif config['incluir_similares']:
            similitud_cat = SequenceMatcher(
                None, 
                str(demanda['categoria']).upper().strip(),
                str(producto['Categoria']).upper().strip()
            ).ratio()
            score += similitud_cat * 25
    
    # 2. Similitud por color (35% del score) - CON LIMPIEZA DE COMAS
    if demanda.get('color') and 'color' in producto and pd.notna(producto['color']):
        if son_colores_iguales_mejorado(demanda['color'], producto['color'], config.get('limpiar_codigos', True)):
            score += 35
        elif config['incluir_similares'] and son_colores_similares_mejorado(demanda['color'], producto['color'], config.get('limpiar_codigos', True)):
            score += 20
    else:
        # Si no hay color, dar puntos parciales
        score += 15
    
    # 3. Similitud por talla (15% del score) - CON OPCIÓN DE IGNORAR
    if config.get('ignorar_tallas', False):
        # Si se ignoran las tallas, dar puntos completos
        score += 15
    else:
        # Usar tallas normalizadas para una comparación más robusta
        talla_demanda = demanda.get('talla_normalizada', demanda.get('talla'))
        talla_producto = producto.get('talla_normalizada', producto.get('talla'))

        if talla_demanda and talla_producto and pd.notna(talla_producto):
            if son_tallas_iguales(talla_demanda, talla_producto):
                score += 15
            elif config['incluir_similares'] and son_tallas_similares(talla_demanda, talla_producto):
                score += 10
        else:
            # Si no hay datos de talla, dar puntos parciales
            score += 8
    
    return score

def determinar_confianza_mejorada(score):
    """Determina el nivel de confianza basado en el score - UMBRALES AJUSTADOS"""
    if score >= 85:
        return 'Alta'
    elif score >= 70:
        return 'Media'
    else:
        return 'Baja'

def buscar_matches_sku_exacto(demanda, df_proveedor):
    """Busca matches exactos por SKU"""
    matches = []
    
    # Para matching por SKU exacto, buscamos por modelo si está disponible
    for _, producto in df_proveedor.iterrows():
        if 'modelo' in producto and pd.notna(producto['modelo']):
            matches.append({
                'sku_proveedor': producto['SKU_Proveedor'],
                'descripcion': producto.get('Descripcion', ''),
                'categoria': producto.get('Categoria', ''),
                'talla': producto.get('talla', ''),
                'color': producto.get('color', ''),
                'precio': producto.get('Precio_Proveedor', 0),
                'stock': producto.get('Stock_Disponible', 0),
                'tipo_match': 'SKU Exacto',
                'score': 100,
                'confianza': 'Alta'
            })
            break  # Solo el primer match exacto
    
    return matches

def buscar_matches_por_atributos_mejorado(demanda, df_proveedor, config):
    """Busca matches por similitud de atributos - VERSION MEJORADA"""
    matches = []
    
    for _, producto in df_proveedor.iterrows():
        score = calcular_score_similitud_mejorado_final(demanda, producto, config)
        
        if score >= config['umbral_similitud']:
            matches.append({
                'sku_proveedor': limpiar_sku_mejorado(producto['SKU_Proveedor'], config.get('limpiar_codigos', True)),
                'descripcion': producto.get('Descripcion', ''),
                'categoria': producto.get('Categoria', ''),
                'talla': producto.get('talla', ''),
                'color': limpiar_codigo_color_mejorado(producto.get('color', ''), config.get('limpiar_codigos', True)),
                'precio': producto.get('Precio_Proveedor', 0),
                'stock': producto.get('Stock_Disponible', 0),
                'tipo_match': 'Atributos Exactos' if score >= 85 else 'Atributos Similares',
                'score': score,
                'confianza': determinar_confianza_mejorada(score)
            })
    
    return matches

def evaluar_matches_para_opciones(matches, demanda, config):
    """Evalúa matches para mostrar opciones (sin calcular cantidades)"""
    for match in matches:
        score_final = match['score']
        
        # Bonus por stock disponible
        if match['stock'] > 0:
            score_final += 5
        
        # Penalty por falta de stock (menor que antes)
        if match['stock'] == 0:
            score_final -= 5
        
        match['score_final'] = max(0, score_final)
    
    # Filtrar por umbral y ordenar
    matches_validos = [m for m in matches if m['score_final'] >= config['umbral_similitud']]
    return sorted(matches_validos, key=lambda x: x['score_final'], reverse=True)

def ejecutar_matching_opciones_mejorado(distribucion, df_proveedor, config):
    """Ejecuta matching mejorado para encontrar opciones disponibles"""
    try:
        opciones_por_demanda = []
        
        for idx, demanda in distribucion.iterrows():
            # Buscar matches según el método seleccionado
            if config['metodo'] == 'Solo SKU Exacto':
                matches = buscar_matches_sku_exacto(demanda, df_proveedor)
            elif config['metodo'] == 'Solo Atributos':
                matches = buscar_matches_por_atributos_mejorado(demanda, df_proveedor, config)
            else:  # Híbrido
                matches_sku = buscar_matches_sku_exacto(demanda, df_proveedor)
                matches_attr = buscar_matches_por_atributos_mejorado(demanda, df_proveedor, config)
                matches = matches_sku + matches_attr
                
                # Eliminar duplicados por SKU
                skus_vistos = set()
                matches_unicos = []
                for match in matches:
                    sku_limpio = limpiar_sku_mejorado(match['sku_proveedor'], config.get('limpiar_codigos', True))
                    if sku_limpio not in skus_vistos:
                        skus_vistos.add(sku_limpio)
                        matches_unicos.append(match)
                matches = matches_unicos
            
            # Evaluar matches
            matches_evaluados = evaluar_matches_para_opciones(matches, demanda, config)
            
            # Filtrar por stock si se requiere
            if config['mostrar_solo_disponibles']:
                matches_evaluados = [m for m in matches_evaluados if m['stock'] > 0]
            
            # Crear opciones para esta demanda
            for match in matches_evaluados:
                opcion = {
                    # Información de la demanda predicha
                    'demanda_id': idx,
                    'categoria_demandada': demanda['categoria'],
                    'talla_demandada': demanda.get('talla'),
                    'color_demandado': demanda.get('color'),
                    'demanda_predicha': demanda['demanda_predicha'],
                    'proporcion_demanda': demanda['proporcion'],
                    
                    # Información del producto del proveedor
                    'sku_proveedor': match['sku_proveedor'],
                    'descripcion_proveedor': match.get('descripcion', ''),
                    'categoria_proveedor': match.get('categoria', ''),
                    'talla_proveedor': match.get('talla', ''),
                    'color_proveedor': match.get('color', ''),
                    'precio_proveedor': match.get('precio', 0),
                    'stock_disponible': match.get('stock', 0),
                    
                    # Información del matching
                    'tipo_match': match['tipo_match'],
                    'score_similitud': match['score'],
                    'confianza': match['confianza'],
                    
                    # Cantidad a pedir (iniciada en 0 para selección manual)
                    'cantidad_a_pedir': 0,
                    'inversion_calculada': 0
                }
                
                opciones_por_demanda.append(opcion)
        
        return pd.DataFrame(opciones_por_demanda) if opciones_por_demanda else None
        
    except Exception as e:
        st.error(f"❌ Error en matching de opciones: {str(e)}")
        return None

def mostrar_debugging_opciones_mejorado(distribucion, df_proveedor, config):
    """Muestra información de debugging mejorada"""
    with st.expander("🔍 Análisis de Problemas - DIAGNÓSTICO AVANZADO", expanded=True):
        st.write("**Diagnóstico del Matching:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Configuración Actual:**")
            st.write(f"• Umbral similitud: {config['umbral_similitud']}%")
            st.write(f"• Ignorar tallas: {'✅' if config.get('ignorar_tallas') else '❌'}")
            st.write(f"• Limpiar códigos: {'✅' if config.get('limpiar_codigos') else '❌'}")
            st.write(f"• Incluir similares: {'✅' if config.get('incluir_similares') else '❌'}")
            
            st.write("**Demanda Predicha (muestra):**")
            st.dataframe(distribucion[['categoria', 'talla', 'color', 'demanda_predicha']].head(3))
        
        with col2:
            st.write("**Productos Disponibles (muestra con limpieza):**")
            df_muestra = df_proveedor[['SKU_Proveedor', 'Categoria', 'color', 'talla']].head(3).copy()
            
            if config.get('limpiar_codigos', True):
                st.write("*Con limpieza de códigos:*")
                df_muestra['color_limpio'] = df_muestra['color'].apply(
                    lambda x: limpiar_codigo_color_mejorado(x, True)
                )
                df_muestra['sku_limpio'] = df_muestra['SKU_Proveedor'].apply(
                    lambda x: limpiar_sku_mejorado(x, True)
                )
            
            st.dataframe(df_muestra)
        
        # Prueba de matching en vivo
        st.write("**🧪 Prueba de Matching en Vivo:**")
        if len(distribucion) > 0 and len(df_proveedor) > 0:
            demanda_prueba = distribucion.iloc[0]
            producto_prueba = df_proveedor.iloc[0]
            
            score_prueba = calcular_score_similitud_mejorado_final(demanda_prueba, producto_prueba, config)
            
            st.write(f"**Ejemplo de Score Calculado:** {score_prueba:.1f}")
            st.write(f"**¿Pasa el umbral?** {'✅ SÍ' if score_prueba >= config['umbral_similitud'] else '❌ NO'}")
            
            # Desglose del score
            with st.expander("Ver desglose del score", expanded=False):
                st.write("**Comparación detallada:**")
                st.write(f"• Demanda: {demanda_prueba['categoria']} | {demanda_prueba.get('talla', 'N/A')} | {demanda_prueba.get('color', 'N/A')}")
                st.write(f"• Proveedor: {producto_prueba.get('Categoria', 'N/A')} | {producto_prueba.get('talla', 'N/A')} | {producto_prueba.get('color', 'N/A')}")
                
                if config.get('limpiar_codigos', True):
                    color_limpio = limpiar_codigo_color_mejorado(producto_prueba.get('color', ''), True)
                    st.write(f"• Color limpio: {color_limpio}")
        
        st.markdown("---")
        st.write("**💡 Sugerencias Automáticas:**")
        
        # Sugerencias automáticas basadas en la configuración
        if config['umbral_similitud'] > 70:
            st.warning("1. **Reducir umbral**: Tu umbral está alto. Prueba con 60-65%")
        
        if not config.get('ignorar_tallas', False):
            st.info("2. **Activar 'Ignorar tallas'**: Esto puede solucionar problemas de tallas incompatibles")
        
        if not config.get('limpiar_codigos', True):
            st.info("3. **Activar 'Limpiar códigos'**: Esto remueve comas que pueden estar causando problemas")
        
        if not config.get('incluir_similares', True):
            st.info("4. **Activar 'Incluir similares'**: Permite matching más flexible")

# =====================================================
# INTERFAZ DE SELECCIÓN MANUAL
# =====================================================

def mostrar_interfaz_seleccion_manual(opciones_disponibles, distribucion):
    """Muestra interfaz para selección manual de cantidades"""
    st.subheader("🛒 Selección Manual de Cantidades")
    
    # Resumen de demanda predicha
    with st.expander("📋 Resumen de Demanda Predicha", expanded=False):
        st.dataframe(distribucion[['categoria', 'talla', 'color', 'demanda_predicha', 'proporcion']], 
                    use_container_width=True)
    
    # Agrupar opciones por demanda
    demandas_unicas = opciones_disponibles['demanda_id'].unique()
    
    # Inicializar cantidades si no existen
    if 'cantidades_seleccionadas' not in st.session_state:
        st.session_state['cantidades_seleccionadas'] = {}
    
    st.markdown("### 🎯 Opciones por Producto Demandado")
    
    for demanda_id in demandas_unicas:
        opciones_demanda = opciones_disponibles[opciones_disponibles['demanda_id'] == demanda_id]
        
        if len(opciones_demanda) == 0:
            continue
            
        # Información de la demanda
        primera_opcion = opciones_demanda.iloc[0]
        demanda_info = f"**{primera_opcion['categoria_demandada']}**"
        if primera_opcion['talla_demandada']:
            demanda_info += f" | Talla: {primera_opcion['talla_demandada']}"
        if primera_opcion['color_demandado']:
            demanda_info += f" | Color: {primera_opcion['color_demandado']}"
        demanda_info += f" | **Demanda Predicha: {primera_opcion['demanda_predicha']:.0f} unidades**"
        
        with st.expander(f"🎯 {demanda_info}", expanded=True):
            mostrar_opciones_para_demanda(opciones_demanda, demanda_id)
    
    # Botones de acción
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Actualizar Totales", type="secondary"):
            actualizar_totales_seleccion()
    
    with col2:
        if st.button("📊 Ver Resumen", type="secondary"):
            mostrar_resumen_seleccion()
    
    with col3:
        if st.button("✅ Finalizar Recomendaciones", type="primary"):
            finalizar_recomendaciones_manuales()

def mostrar_opciones_para_demanda(opciones_demanda, demanda_id):
    """Muestra las opciones disponibles para una demanda específica"""
    
    # Ordenar por score de similitud
    opciones_ordenadas = opciones_demanda.sort_values('score_similitud', ascending=False)
    
    # Crear tabla interactiva
    st.markdown("**Opciones Disponibles:**")
    
    # Headers de la tabla
    cols = st.columns([0.25, 0.25, 0.15, 0.1, 0.1, 0.15])
    with cols[0]:
        st.markdown("**SKU Proveedor**")
    with cols[1]:
        st.markdown("**Descripción**")
    with cols[2]:
        st.markdown("**Precio**")
    with cols[3]:
        st.markdown("**Stock**")
    with cols[4]:
        st.markdown("**Score**")
    with cols[5]:
        st.markdown("**Cantidad**")
    
    # Filas de opciones
    for idx, (_, opcion) in enumerate(opciones_ordenadas.iterrows()):
        key_cantidad = f"cantidad_{demanda_id}_{idx}"
        
        cols = st.columns([0.25, 0.25, 0.15, 0.1, 0.1, 0.15])
        
        with cols[0]:
            # SKU con indicador de match
            match_icon = "🎯" if opcion['score_similitud'] >= 85 else "✅" if opcion['score_similitud'] >= 70 else "⚠️"
            st.write(f"{match_icon} {opcion['sku_proveedor']}")
        
        with cols[1]:
            # Descripción truncada
            desc = str(opcion['descripcion_proveedor'])[:25]
            if len(str(opcion['descripcion_proveedor'])) > 25:
                desc += "..."
            st.write(desc)
        
        with cols[2]:
            # Precio
            precio = opcion['precio_proveedor']
            if precio > 0:
                st.write(f"${precio:,.2f}")
            else:
                st.write("N/A")
        
        with cols[3]:
            # Stock con color
            stock = opcion['stock_disponible']
            if stock > 0:
                st.success(f"{stock:,}")
            else:
                st.error("Sin stock")
        
        with cols[4]:
            # Score
            score = opcion['score_similitud']
            if score >= 85:
                st.success(f"{score:.0f}")
            elif score >= 70:
                st.info(f"{score:.0f}")
            else:
                st.warning(f"{score:.0f}")
        
        with cols[5]:
            # Input de cantidad
            max_cantidad = max(100, int(opcion['stock_disponible']) if opcion['stock_disponible'] > 0 else 100)
            cantidad = st.number_input(
                "Qty",
                min_value=0,
                max_value=max_cantidad,
                value=st.session_state['cantidades_seleccionadas'].get(key_cantidad, 0),
                step=1,
                key=key_cantidad,
                label_visibility="collapsed"
            )
            
            # Guardar cantidad seleccionada
            st.session_state['cantidades_seleccionadas'][key_cantidad] = cantidad
        
        # Mostrar detalles del match si es necesario
        if opcion['score_similitud'] < 85:
            with st.expander(f"ℹ️ Detalles del match - {opcion['sku_proveedor']}", expanded=False):
                col_det1, col_det2 = st.columns(2)
                
                with col_det1:
                    st.write("**Demandado:**")
                    st.write(f"• Categoría: {opcion['categoria_demandada']}")
                    st.write(f"• Talla: {opcion['talla_demandada'] or 'N/A'}")
                    st.write(f"• Color: {opcion['color_demandado'] or 'N/A'}")
                
                with col_det2:
                    st.write("**Proveedor:**")
                    st.write(f"• Categoría: {opcion['categoria_proveedor'] or 'N/A'}")
                    st.write(f"• Talla: {opcion['talla_proveedor'] or 'N/A'}")
                    st.write(f"• Color: {opcion['color_proveedor'] or 'N/A'}")
                
                st.write(f"**Tipo de Match:** {opcion['tipo_match']} | **Confianza:** {opcion['confianza']}")

def actualizar_totales_seleccion():
    """Actualiza los totales basados en las cantidades seleccionadas"""
    opciones = st.session_state.get('opciones_disponibles')
    if opciones is None:
        return
    
    # Actualizar cantidades e inversiones
    opciones_actualizadas = opciones.copy()
    opciones_actualizadas['cantidad_a_pedir'] = 0
    opciones_actualizadas['inversion_calculada'] = 0
    
    for key, cantidad in st.session_state['cantidades_seleccionadas'].items():
        if cantidad > 0:
            # Extraer información de la key
            parts = key.split('_')
            if len(parts) >= 3:
                demanda_id = int(parts[1])
                idx = int(parts[2])
                
                # Encontrar la fila correspondiente
                opciones_demanda = opciones[opciones['demanda_id'] == demanda_id]
                if len(opciones_demanda) > idx:
                    opciones_ordenadas = opciones_demanda.sort_values('score_similitud', ascending=False)
                    if len(opciones_ordenadas) > idx:
                        fila_actual = opciones_ordenadas.iloc[idx]
                        sku = fila_actual['sku_proveedor']
                        
                        # Actualizar DataFrame
                        mask = (opciones_actualizadas['sku_proveedor'] == sku) & (opciones_actualizadas['demanda_id'] == demanda_id)
                        opciones_actualizadas.loc[mask, 'cantidad_a_pedir'] = cantidad
                        opciones_actualizadas.loc[mask, 'inversion_calculada'] = cantidad * fila_actual['precio_proveedor']
    
    st.session_state['opciones_disponibles'] = opciones_actualizadas
    st.success("✅ Totales actualizados")

def mostrar_resumen_seleccion():
    """Muestra resumen de la selección actual"""
    opciones = st.session_state.get('opciones_disponibles')
    if opciones is None:
        st.warning("No hay opciones disponibles")
        return
    
    # Filtrar solo productos con cantidad > 0
    seleccionados = opciones[opciones['cantidad_a_pedir'] > 0].copy()
    
    if len(seleccionados) == 0:
        st.warning("⚠️ No has seleccionado ningún producto")
        return
    
    st.subheader("📊 Resumen de Selección")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_productos = len(seleccionados)
        st.metric("Productos Seleccionados", total_productos)
    
    with col2:
        total_cantidad = seleccionados['cantidad_a_pedir'].sum()
        st.metric("Cantidad Total", f"{total_cantidad:,}")
    
    with col3:
        # Recalcular inversión
        seleccionados['inversion_real'] = seleccionados['cantidad_a_pedir'] * seleccionados['precio_proveedor']
        total_inversion = seleccionados['inversion_real'].sum()
        st.metric("Inversión Total", f"${total_inversion:,.2f}")
    
    with col4:
        precio_promedio = seleccionados['precio_proveedor'].mean()
        st.metric("Precio Promedio", f"${precio_promedio:.2f}")
    
    # Tabla de seleccionados
    st.subheader("🛒 Productos Seleccionados")
    
    # Preparar tabla de resumen
    tabla_resumen = seleccionados[[
        'categoria_demandada', 'talla_demandada', 'color_demandado',
        'sku_proveedor', 'descripcion_proveedor', 'cantidad_a_pedir',
        'precio_proveedor', 'stock_disponible', 'score_similitud'
    ]].copy()
    
    tabla_resumen['inversion'] = tabla_resumen['cantidad_a_pedir'] * tabla_resumen['precio_proveedor']
    tabla_resumen = tabla_resumen.round(2)
    
    st.dataframe(tabla_resumen, use_container_width=True)
    
    # Análisis por demanda
    st.subheader("📈 Cumplimiento de Demanda")
    
    # Agrupar por demanda para ver cumplimiento
    cumplimiento = []
    for demanda_id in seleccionados['demanda_id'].unique():
        items_demanda = seleccionados[seleccionados['demanda_id'] == demanda_id]
        demanda_predicha = items_demanda['demanda_predicha'].iloc[0]
        cantidad_seleccionada = items_demanda['cantidad_a_pedir'].sum()
        
        cumplimiento.append({
            'Producto': f"{items_demanda['categoria_demandada'].iloc[0]} | "
                       f"{items_demanda['talla_demandada'].iloc[0] or 'N/A'} | "
                       f"{items_demanda['color_demandado'].iloc[0] or 'N/A'}",
            'Demanda_Predicha': demanda_predicha,
            'Cantidad_Seleccionada': cantidad_seleccionada,
            'Cumplimiento_%': (cantidad_seleccionada / demanda_predicha * 100) if demanda_predicha > 0 else 0
        })
    
    df_cumplimiento = pd.DataFrame(cumplimiento)
    st.dataframe(df_cumplimiento.round(1), use_container_width=True)

def finalizar_recomendaciones_manuales():
    """Finaliza las recomendaciones con selección manual"""
    opciones = st.session_state.get('opciones_disponibles')
    if opciones is None:
        st.error("No hay opciones disponibles")
        return
    
    # Filtrar solo productos con cantidad > 0
    recomendaciones_finales = opciones[opciones['cantidad_a_pedir'] > 0].copy()
    
    if len(recomendaciones_finales) == 0:
        st.error("❌ No has seleccionado ningún producto")
        return
    
    # Recalcular inversiones
    recomendaciones_finales['inversion_total'] = (
        recomendaciones_finales['cantidad_a_pedir'] * 
        recomendaciones_finales['precio_proveedor']
    )
    
    # Renombrar columnas para compatibilidad
    recomendaciones_finales = recomendaciones_finales.rename(columns={
        'categoria_demandada': 'categoria',
        'talla_demandada': 'talla',
        'color_demandado': 'color',
        'cantidad_a_pedir': 'cantidad_recomendada'
    })
    
    # Guardar recomendaciones finales
    st.session_state['recomendaciones_finales'] = recomendaciones_finales
    
    st.success("✅ Recomendaciones finalizadas exitosamente")
    
    # Mostrar recomendaciones finales
    mostrar_recomendaciones_finales_manual(recomendaciones_finales)

def mostrar_recomendaciones_finales_manual(recomendaciones):
    """Muestra las recomendaciones finales con selección manual"""
    st.subheader("📋 Recomendaciones Finales")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", len(recomendaciones))
    
    with col2:
        cantidad_total = recomendaciones['cantidad_recomendada'].sum()
        st.metric("Cantidad Total", f"{cantidad_total:,}")
    
    with col3:
        inversion_total = recomendaciones['inversion_total'].sum()
        st.metric("Inversión Total", f"${inversion_total:,.0f}")
    
    with col4:
        score_promedio = recomendaciones['score_similitud'].mean()
        st.metric("Score Promedio", f"{score_promedio:.1f}")
    
    # Tabla de recomendaciones
    st.subheader("📊 Tabla de Recomendaciones")
    
    # Preparar datos para mostrar
    columnas_mostrar = [
        'categoria', 'talla', 'color', 'sku_proveedor', 'descripcion_proveedor',
        'cantidad_recomendada', 'precio_proveedor', 'inversion_total',
        'stock_disponible', 'tipo_match', 'score_similitud', 'confianza'
    ]
    
    df_mostrar = recomendaciones[columnas_mostrar].copy()
    df_mostrar = df_mostrar.sort_values('score_similitud', ascending=False)
    
    # Formatear números
    df_mostrar['cantidad_recomendada'] = df_mostrar['cantidad_recomendada'].round(0).astype(int)
    df_mostrar['precio_proveedor'] = df_mostrar['precio_proveedor'].round(2)
    df_mostrar['inversion_total'] = df_mostrar['inversion_total'].round(0).astype(int)
    df_mostrar['score_similitud'] = df_mostrar['score_similitud'].round(1)
    
    st.dataframe(df_mostrar, use_container_width=True)
    
    # Análisis por categoría
    mostrar_analisis_por_categoria(recomendaciones)
    
    # Opciones de descarga
    generar_descargas(recomendaciones)

def mostrar_analisis_por_categoria(df):
    """Muestra análisis agrupado por categoría"""
    st.subheader("📈 Análisis por Categoría")
    
    resumen_cat = df.groupby('categoria').agg({
        'cantidad_recomendada': 'sum',
        'inversion_total': 'sum',
        'precio_proveedor': 'mean',
        'sku_proveedor': 'count'
    }).round(2)
    
    resumen_cat.columns = ['Cantidad', 'Inversión ($)', 'Precio Prom ($)', 'Productos']
    resumen_cat = resumen_cat.sort_values('Inversión ($)', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(resumen_cat, use_container_width=True)
    
    with col2:
        # Gráfica de inversión por categoría
        fig_cat = px.bar(
            x=resumen_cat['Inversión ($)'],
            y=resumen_cat.index,
            orientation='h',
            title="Inversión por Categoría",
            color=resumen_cat['Inversión ($)'],
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_cat, use_container_width=True)

def generar_descargas(df):
    """Genera archivos de descarga"""
    st.subheader("💾 Descargar Recomendaciones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Descargar CSV",
            csv,
            f"recomendaciones_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )
    
    with col2:
        # Excel
        try:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Recomendaciones', index=False)
                
                # Resumen por categoría
                if 'categoria' in df.columns:
                    resumen = df.groupby('categoria').agg({
                        'cantidad_recomendada': 'sum',
                        'inversion_total': 'sum'
                    })
                    resumen.to_excel(writer, sheet_name='Resumen')
            
            buffer.seek(0)
            
            st.download_button(
                "📊 Descargar Excel",
                buffer.getvalue(),
                f"recomendaciones_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except:
            st.info("Excel no disponible")
    
    with col3:
        # Reporte
        if st.button("📄 Generar Reporte"):
            generar_reporte_final(df)

def generar_reporte_final(df):
    """Genera reporte final en texto"""
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    reporte = f"""
REPORTE DE RECOMENDACIONES DE COMPRA
===================================
Fecha: {fecha}

RESUMEN EJECUTIVO
-----------------
• Total productos seleccionados: {len(df):,}
• Cantidad total: {df['cantidad_recomendada'].sum():,} unidades
• Inversión total: ${df['inversion_total'].sum():,.2f}
• Score promedio: {df['score_similitud'].mean():.1f}

DISTRIBUCIÓN POR TIPO DE MATCH
------------------------------"""
    
    tipo_dist = df['tipo_match'].value_counts()
    for tipo, cantidad in tipo_dist.items():
        porcentaje = (cantidad / len(df)) * 100
        reporte += f"\n• {tipo}: {cantidad} productos ({porcentaje:.1f}%)"
    
    reporte += f"""

TOP 10 RECOMENDACIONES
---------------------"""
    
    top_10 = df.nlargest(10, 'inversion_total')
    for _, row in top_10.iterrows():
        reporte += f"""
• SKU: {row['sku_proveedor']}
  Categoría: {row['categoria']} | Cantidad: {row['cantidad_recomendada']}
  Inversión: ${row['inversion_total']:,.2f} | Score: {row['score_similitud']:.1f}
"""
    
    reporte += f"""

RECOMENDACIONES
--------------
• Priorizar productos con score ≥ 80
• Verificar disponibilidad de stock con proveedor
• Considerar negociación por volumen
• Revisar tendencias estacionales

MEJORAS IMPLEMENTADAS EN ESTA VERSIÓN
------------------------------------
• ✅ Solución al problema de comas en códigos de color (1,001 = 1001)
• ✅ Opción para ignorar diferencias de tallas incompatibles
• ✅ Algoritmo de matching más flexible y robusto
• ✅ Debugging avanzado para identificar problemas

---
Generado por Sistema de Recomendaciones IA - Versión Mejorada
"""
    
    st.text_area("📄 Reporte Final", reporte, height=400)
    
    st.download_button(
        "💾 Descargar Reporte",
        reporte,
        f"reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        "text/plain"
    )

# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================

if __name__ == "__main__":
    try:
        # Verificar dependencias
        import plotly.express as px
        import pandas as pd
        import numpy as np
        
        # Ejecutar aplicación
        main()
        
    except ImportError as e:
        st.error(f"❌ Dependencia faltante: {str(e)}")
        st.info("💡 Instala con: pip install streamlit pandas plotly prophet openpyxl")
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        st.info("🔄 Recarga la página para reiniciar")import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
from io import BytesIO
import re
from difflib import SequenceMatcher

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="🛒 Sistema de Recomendaciones de Compra IA",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal de la aplicación"""
    st.title("🛒 Sistema de Recomendaciones de Compra con IA")
    st.markdown("### 📈 Predicción de Demanda + Matching Inteligente con Proveedor")
    
    # Sidebar con progreso
    with st.sidebar:
        st.markdown("## 📋 Progreso del Proceso")
        
        # Estado del proceso
        paso_actual = get_current_step()
        
        pasos = [
            ("1️⃣", "Cargar Datos Históricos", paso_actual >= 1),
            ("2️⃣", "Generar Predicción", paso_actual >= 2),
            ("3️⃣", "Cargar Catálogo Proveedor", paso_actual >= 3),
            ("4️⃣", "Seleccionar Productos", paso_actual >= 4)
        ]
        
        for icono, nombre, completado in pasos:
            if completado:
                st.success(f"{icono} {nombre} ✅")
            else:
                st.info(f"{icono} {nombre}")
        
        st.markdown("---")
        
        # Información adicional si hay datos cargados
        if 'df_ventas' in st.session_state:
            df = st.session_state['df_ventas']
            st.markdown("### 📊 Datos Cargados")
            st.metric("Registros", f"{len(df):,}")
            st.metric("Marcas", df['Marca'].nunique())
            st.metric("Periodo", f"{(df['Fecha'].max() - df['Fecha'].min()).days} días")
    
    # Contenido principal
    if paso_actual == 0:
        mostrar_paso_1_carga_datos()
    elif paso_actual == 1:
        mostrar_paso_2_prediccion()
    elif paso_actual == 2:
        mostrar_paso_3_carga_proveedor()
    elif paso_actual >= 3:
        mostrar_paso_4_seleccion_manual()

def get_current_step():
    """Determina el paso actual del proceso"""
    if 'recomendaciones_finales' in st.session_state:
        return 4
    elif 'df_proveedor' in st.session_state:
        return 3
    elif 'predicciones' in st.session_state:
        return 2
    elif 'df_ventas' in st.session_state:
        return 1
    else:
        return 0

# =====================================================
# PASO 1: CARGA DE DATOS HISTÓRICOS
# =====================================================

def mostrar_paso_1_carga_datos():
    """Paso 1: Carga y procesamiento de datos históricos"""
    st.header("1️⃣ Carga de Datos Históricos de Ventas")
    
    # Información sobre el formato esperado
    with st.expander("📋 Formato de Datos Esperado", expanded=True):
        st.markdown("""
        **Columnas Requeridas:**
        - `Fecha`: Fecha de la venta
        - `Marca`: Marca del producto  
        - `Parte`: SKU del producto
        - `Categoría`: Categoría del producto
        
        **Columnas Opcionales (recomendadas):**
        - `talla`, `color`, `modelo`: Para matching avanzado
        - `PrecioSinIVA`: Para análisis financiero
        - `Movimiento`: Canal de venta
        - `OrderDtl_DiscountPercent`: Descuentos aplicados
        
        **Formatos soportados:** CSV, Excel (.xlsx, .xls)
        """)
    
    # Upload del archivo
    uploaded_file = st.file_uploader(
        "📁 Sube tu archivo de ventas históricas",
        type=['csv', 'xlsx', 'xls'],
        help="Archivo con el histórico de ventas"
    )
    
    if uploaded_file is not None:
        with st.spinner("🔄 Procesando archivo..."):
            df_ventas = cargar_y_procesar_datos(uploaded_file)
            
            if df_ventas is not None:
                st.session_state['df_ventas'] = df_ventas
                st.success(f"✅ Datos cargados exitosamente: {len(df_ventas):,} registros")
                
                # Mostrar vista previa y estadísticas
                mostrar_resumen_datos_cargados(df_ventas)
                
                # Botón para continuar
                if st.button("➡️ Continuar a Predicción", type="primary"):
                    st.rerun()
            else:
                st.error("❌ Error al procesar el archivo")

def cargar_y_procesar_datos(uploaded_file):
    """Carga y procesa el archivo de datos"""
    try:
        # Cargar archivo según el tipo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Verificar columnas críticas
        columnas_criticas = ['Fecha', 'Marca', 'Parte']
        columnas_faltantes = [col for col in columnas_criticas if col not in df.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan columnas críticas: {', '.join(columnas_faltantes)}")
            return None
        
        # Procesar fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])
        
        # Limpiar y estandarizar datos
        df = limpiar_datos(df)
        
        # Filtrar datos válidos
        df = df.dropna(subset=['Fecha', 'Marca', 'Parte'])
        
        if len(df) == 0:
            st.error("❌ No quedan datos válidos después del procesamiento")
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error al cargar archivo: {str(e)}")
        return None

def limpiar_datos(df):
    """Limpia y estandariza los datos"""
    df = df.copy()
    
    # Limpiar categorías si existe la columna
    if 'Categoría' in df.columns:
        df['categoria_limpia'] = df['Categoría'].apply(limpiar_categoria)
    
    # Procesar descuentos si existe
    if 'OrderDtl_DiscountPercent' in df.columns:
        df['OrderDtl_DiscountPercent'] = pd.to_numeric(df['OrderDtl_DiscountPercent'], errors='coerce').fillna(0)
        df['Tiene_Descuento'] = df['OrderDtl_DiscountPercent'] > 0
    
    # Procesar precios si existe
    if 'PrecioSinIVA' in df.columns:
        df['PrecioSinIVA'] = pd.to_numeric(df['PrecioSinIVA'], errors='coerce').fillna(0)
    
    # Extraer información del SKU si no existe por separado
    if 'modelo' not in df.columns and 'Parte' in df.columns:
        df['modelo'] = df['Parte'].apply(extraer_modelo_sku)
    
    if 'talla' not in df.columns and 'Parte' in df.columns:
        extraidos = df['Parte'].apply(extraer_color_talla_sku)
        df['talla'] = extraidos.apply(lambda d: d.get('talla'))
        df['color'] = extraidos.apply(lambda d: d.get('color'))

    # Crear columna de talla normalizada para comparaciones consistentes
    if 'talla' in df.columns:
        df['talla_normalizada'] = df['talla'].apply(normalizar_talla)
    else:
        df['talla_normalizada'] = None

    return df

def limpiar_categoria(categoria):
    """Limpia y clasifica una categoría de producto"""
    if pd.isna(categoria) or categoria == "":
        return "Sin Categoría"

    categoria = str(categoria).upper().strip()

    clasificaciones = {
        "CALZADO": ["CALZADO", "SHOES", "SNEAKERS", "SANDAL", "BOOT", "ZAPATO"],
        "ACCESORIOS": ["ACCESORIO", "HANDBAG", "BAG", "BOLSA", "BACKPACK", "HAT", "BELT", "WALLET"],
        "LENTES": ["SUNGLASS", "GLASSES", "LENTES", "GAFAS"],
        "PLAYERAS": ["PLAYERA", "T-SHIRT", "TSHIRT", "TEE", "POLO"],
        "JEANS": ["JEAN", "DENIM", "PANTALON"],
        "BUFANDAS": ["SCARF", "SCARVES", "BUFANDA"],
        "CHAMARRAS": ["CHAMARRA", "JACKET", "COAT", "ABRIGO"],
        "VESTIDOS": ["DRESS", "VESTIDO"],
        "FALDAS": ["SKIRT", "FALDA"],
        "SHORTS": ["SHORT", "BERMUDA"],
        "PERFUMES": ["PARFUM", "PERFUME", "FRAGRANCE", "COLOGNE", "EDC", "EDT", "EDP"],
    }

    for categoria_limpia, palabras_clave in clasificaciones.items():
        for palabra in palabras_clave:
            if palabra in categoria:
                return categoria_limpia

    return categoria[:30]

def extraer_modelo_sku(sku):
    """Extrae el modelo de un SKU"""
    if not isinstance(sku, str):
        return None
    return sku.strip().split("_")[0] if sku.strip() else None

def extraer_color_talla_sku(parte):
    """Extrae color y talla de la columna 'Parte' (SKU)"""
    if not isinstance(parte, str):
        return {"color": None, "talla": None}

    partes = parte.strip().split("_")

    if len(partes) >= 3:
        color = partes[-2] or None
        talla = partes[-1] or None
        return {"color": color, "talla": talla}
    elif len(partes) == 2:
        talla = partes[1] or None
        return {"color": None, "talla": talla}

    return {"color": None, "talla": None}

def mostrar_resumen_datos_cargados(df):
    """Muestra resumen de los datos cargados"""
    st.subheader("📊 Resumen de Datos Cargados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Registros", f"{len(df):,}")
    
    with col2:
        st.metric("Marcas Únicas", df['Marca'].nunique())
    
    with col3:
        if 'categoria_limpia' in df.columns:
            st.metric("Categorías", df['categoria_limpia'].nunique())
        elif 'Categoría' in df.columns:
            st.metric("Categorías", df['Categoría'].nunique())
    
    with col4:
        rango_dias = (df['Fecha'].max() - df['Fecha'].min()).days
        st.metric("Días de Historia", rango_dias)
    
    # Top marcas
    st.subheader("🏷️ Top Marcas por Volumen")
    top_marcas = df['Marca'].value_counts().head(10)
    
    fig_marcas = px.bar(
        x=top_marcas.values,
        y=top_marcas.index,
        orientation='h',
        title="Top 10 Marcas por Número de Ventas"
    )
    st.plotly_chart(fig_marcas, use_container_width=True)
    
    # Vista previa de datos
    st.subheader("👀 Vista Previa de Datos")
    st.dataframe(df.head(10), use_container_width=True)

# =====================================================
# PASO 2: PREDICCIÓN DE DEMANDA
# =====================================================

def mostrar_paso_2_prediccion():
    """Paso 2: Generar predicción de demanda"""
    st.header("2️⃣ Predicción de Demanda con Prophet")
    
    df_ventas = st.session_state['df_ventas']
    
    # Configuración de la predicción
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Configuración")
        
        # Selección de marca
        marcas_disponibles = sorted(df_ventas['Marca'].unique())
        marca_seleccionada = st.selectbox("🏷️ Seleccionar Marca", marcas_disponibles)
        
        # Parámetros de predicción
        periodos_futuros = st.slider("📅 Días a predecir", 30, 180, 90)
        factor_seguridad = st.slider("🛡️ Factor de seguridad", 1.0, 2.5, 1.3, 0.1)
        
        # Filtros adicionales
        aplicar_filtros = st.checkbox("🔍 Aplicar filtros avanzados")
        
        filtros = {}
        if aplicar_filtros:
            if 'Movimiento' in df_ventas.columns:
                canales = ['Todos'] + sorted(df_ventas['Movimiento'].dropna().unique())
                filtros['canal'] = st.selectbox("🏪 Canal", canales)
            
            if 'Tiene_Descuento' in df_ventas.columns:
                filtros['descuento'] = st.selectbox("💰 Descuentos", 
                    ['Todos', 'Solo con descuento', 'Solo sin descuento'])
    
    with col2:
        st.subheader("📊 Datos de la Marca Seleccionada")
        
        # Filtrar datos por marca
        df_marca = df_ventas[df_ventas['Marca'] == marca_seleccionada]
        
        # Aplicar filtros adicionales
        df_filtrado = aplicar_filtros_prediccion(df_marca, filtros)
        
        # Métricas de la marca
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Ventas", f"{len(df_filtrado):,}")
            st.metric("SKUs Únicos", df_filtrado['Parte'].nunique())
        
        with col_b:
            if 'categoria_limpia' in df_filtrado.columns:
                st.metric("Categorías", df_filtrado['categoria_limpia'].nunique())
            rango_dias = (df_filtrado['Fecha'].max() - df_filtrado['Fecha'].min()).days
            st.metric("Días de Historia", rango_dias)
    
    # Generar predicción
    if st.button("🔮 Generar Predicción con Prophet", type="primary"):
        with st.spinner("🤖 Generando predicción con IA..."):
            predicciones = generar_prediccion_prophet(df_filtrado, periodos_futuros)
            
            if predicciones is not None:
                # Calcular distribución de demanda
                distribucion = calcular_distribucion_demanda(df_filtrado, predicciones, factor_seguridad)
                
                # Guardar en session state
                st.session_state['predicciones'] = predicciones
                st.session_state['distribucion_demanda'] = distribucion
                st.session_state['marca_seleccionada'] = marca_seleccionada
                
                st.success("✅ Predicción generada exitosamente")
                
                # Mostrar resultados
                mostrar_resultados_prediccion(predicciones, distribucion)
                
                # Botón para continuar
                if st.button("➡️ Continuar a Carga de Proveedor", type="primary"):
                    st.rerun()

def aplicar_filtros_prediccion(df, filtros):
    """Aplica filtros adicionales para la predicción"""
    df_filtrado = df.copy()
    
    if filtros.get('canal') and filtros['canal'] != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Movimiento'] == filtros['canal']]
    
    if filtros.get('descuento'):
        if filtros['descuento'] == 'Solo con descuento':
            df_filtrado = df_filtrado[df_filtrado['Tiene_Descuento'] == True]
        elif filtros['descuento'] == 'Solo sin descuento':
            df_filtrado = df_filtrado[df_filtrado['Tiene_Descuento'] == False]
    
    return df_filtrado

def generar_prediccion_prophet(df_filtrado, periodos):
    """Genera predicción usando Prophet"""
    try:
        from prophet import Prophet
        
        # Preparar datos para Prophet
        df_prophet = df_filtrado.groupby('Fecha').size().reset_index(name='y')
        df_prophet = df_prophet.rename(columns={'Fecha': 'ds'})
        df_prophet = df_prophet.sort_values('ds')
        
        if len(df_prophet) < 10:
            st.error("❌ Datos insuficientes para generar predicción (mínimo 10 días)")
            return None
        
        # Crear y entrenar modelo Prophet
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            seasonality_mode='multiplicative',
            interval_width=0.95
        )
        
        model.fit(df_prophet)
        
        # Crear fechas futuras
        future = model.make_future_dataframe(periods=periodos)
        forecast = model.predict(future)
        
        return {
            'historico': df_prophet,
            'prediccion': forecast,
            'modelo': model,
            'demanda_total_predicha': forecast[forecast['ds'] > df_filtrado['Fecha'].max()]['yhat'].sum()
        }
        
    except ImportError:
        st.error("❌ Prophet no está instalado. Instala con: pip install prophet")
        return None
    except Exception as e:
        st.error(f"❌ Error en predicción: {str(e)}")
        return None

def calcular_distribucion_demanda(df_ventas, predicciones, factor_seguridad):
    """Calcula distribución de demanda por atributos"""
    demanda_total = predicciones['demanda_total_predicha'] * factor_seguridad
    
    # Determinar columnas disponibles para distribución
    col_categoria = 'categoria_limpia' if 'categoria_limpia' in df_ventas.columns else 'Categoría'
    
    distribuciones = []
    
    # Distribución por categoría + atributos
    if all(col in df_ventas.columns for col in [col_categoria, 'talla', 'color']):
        # Distribución completa
        dist_completa = df_ventas.groupby([col_categoria, 'talla', 'color']).size()
        dist_completa_norm = dist_completa / len(df_ventas)
        
        for (categoria, talla, color), proporcion in dist_completa_norm.items():
            demanda_item = demanda_total * proporcion
            if demanda_item >= 1:  # Filtrar demandas muy pequeñas
                distribuciones.append({
                    'categoria': categoria,
                    'talla': talla,
                    'color': color,
                    'demanda_predicha': demanda_item,
                    'proporcion': proporcion
                })
    
    elif col_categoria in df_ventas.columns:
        # Solo por categoría
        dist_categoria = df_ventas[col_categoria].value_counts(normalize=True)
        
        for categoria, proporcion in dist_categoria.items():
            demanda_item = demanda_total * proporcion
            distribuciones.append({
                'categoria': categoria,
                'talla': None,
                'color': None,
                'demanda_predicha': demanda_item,
                'proporcion': proporcion
            })
    
    return pd.DataFrame(distribuciones).sort_values('demanda_predicha', ascending=False)

def mostrar_resultados_prediccion(predicciones, distribucion):
    """Muestra los resultados de la predicción"""
    st.subheader("📈 Resultados de la Predicción")
    
    # Gráfica de predicción
    mostrar_grafica_prediccion(predicciones)
    
    # Métricas de predicción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        demanda_total = predicciones['demanda_total_predicha']
        st.metric("Demanda Total Predicha", f"{demanda_total:,.0f}")
    
    with col2:
        forecast = predicciones['prediccion']
        historico = predicciones['historico']
        prediccion_futura = forecast[forecast['ds'] > historico['ds'].max()]
        promedio_diario = demanda_total / len(prediccion_futura)
        st.metric("Promedio Diario", f"{promedio_diario:.1f}")
    
    with col3:
        crecimiento = ((prediccion_futura['yhat'].mean() / historico['y'].mean()) - 1) * 100
        st.metric("Crecimiento Esperado", f"{crecimiento:+.1f}%")
    
    # Top distribución de demanda
    if len(distribucion) > 0:
        st.subheader("🎯 Distribución de Demanda por Productos")
        
        top_distribucion = distribucion.head(15)
        
        # Crear etiquetas
        if 'talla' in top_distribucion.columns and 'color' in top_distribucion.columns:
            top_distribucion['etiqueta'] = top_distribucion.apply(
                lambda row: f"{row['categoria']} | {row['talla'] or 'N/A'} | {row['color'] or 'N/A'}", axis=1
            )
        else:
            top_distribucion['etiqueta'] = top_distribucion['categoria']
        
        fig_dist = px.bar(
            top_distribucion,
            x='demanda_predicha',
            y='etiqueta',
            orientation='h',
            title="Top 15 Productos por Demanda Predicha",
            color='demanda_predicha',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_dist, use_container_width=True)

def mostrar_grafica_prediccion(predicciones):
    """Muestra gráfica de la predicción"""
    forecast = predicciones['prediccion']
    historico = predicciones['historico']
    
    fig = go.Figure()
    
    # Datos históricos
    fig.add_trace(go.Scatter(
        x=historico['ds'],
        y=historico['y'],
        mode='lines+markers',
        name='Ventas Históricas',
        line=dict(color='blue', width=2)
    ))
    
    # Predicción futura
    prediccion_futura = forecast[forecast['ds'] > historico['ds'].max()]
    
    fig.add_trace(go.Scatter(
        x=prediccion_futura['ds'],
        y=prediccion_futura['yhat'],
        mode='lines+markers',
        name='Predicción',
        line=dict(color='red', dash='dash', width=2)
    ))
    
    # Intervalo de confianza
    fig.add_trace(go.Scatter(
        x=prediccion_futura['ds'],
        y=prediccion_futura['yhat_upper'],
        fill=None,
        mode='lines',
        line_color='rgba(0,100,80,0)',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=prediccion_futura['ds'],
        y=prediccion_futura['yhat_lower'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,100,80,0)',
        name='Intervalo de Confianza',
        fillcolor='rgba(255,0,0,0.2)'
    ))
    
    fig.update_layout(
        title="📈 Predicción de Demanda",
        xaxis_title="Fecha",
        yaxis_title="Cantidad de Ventas",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# PASO 3: CARGA DEL PROVEEDOR
# =====================================================

def mostrar_paso_3_carga_proveedor():
    """Paso 3: Carga del catálogo del proveedor"""
    st.header("3️⃣ Carga del Catálogo del Proveedor")
    
    marca_seleccionada = st.session_state.get('marca_seleccionada', 'N/A')
    st.info(f"🏷️ Marca seleccionada: **{marca_seleccionada}**")
    
    # Información sobre el formato del proveedor
    with st.expander("📋 Formato del Catálogo del Proveedor", expanded=True):
        st.markdown("""
        **Columnas Requeridas:**
        - `SKU/Código`: Identificador único del producto
        
        **Columnas Opcionales (recomendadas):**
        - `Precio`: Precio de compra o wholesale
        - `Descripción`: Nombre o descripción del producto
        - `Categoría`: Tipo de producto
        - `Stock/Cantidad`: Inventario disponible
        - `Talla`: Talla del producto
        - `Color`: Color del producto
        
        **Formatos soportados:** CSV, Excel (.xlsx, .xls)
        """)
    
    # Upload del archivo del proveedor
    uploaded_proveedor = st.file_uploader(
        f"📁 Sube el catálogo del proveedor para {marca_seleccionada}",
        type=['csv', 'xlsx', 'xls'],
        help="Archivo con los productos disponibles del proveedor"
    )
    
    if uploaded_proveedor is not None:
        with st.spinner("🔄 Procesando catálogo del proveedor..."):
            df_proveedor = cargar_archivo_proveedor(uploaded_proveedor)
            
            if df_proveedor is not None:
                # Mostrar vista previa
                st.subheader("👀 Vista Previa del Catálogo")
                st.dataframe(df_proveedor.head(10), use_container_width=True)
                
                # Configurar mapeo de columnas
                configurar_mapeo_columnas(df_proveedor, marca_seleccionada)

def cargar_archivo_proveedor(uploaded_file):
    """Carga el archivo del proveedor con selección de hoja para Excel"""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Para CSV, cargar directamente
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            
            # Limpiar filas completamente vacías
            df = df.dropna(how='all')
            
            if len(df) == 0:
                st.error("❌ El archivo está vacío o solo contiene filas vacías")
                return None
            
            st.success(f"✅ Catálogo CSV cargado: {len(df):,} filas")
            return df
            
        else:
            # Para Excel, primero mostrar las hojas disponibles
            try:
                # Leer todas las hojas para mostrar opciones
                excel_file = pd.ExcelFile(uploaded_file)
                hojas_disponibles = excel_file.sheet_names
                
                st.subheader("📋 Seleccionar Hoja de Excel")
                
                # Mostrar información de las hojas
                col1, col2 = st.columns(2)
                
                with col1:
                    # Selector de hoja
                    hoja_seleccionada = st.selectbox(
                        "🗂️ Selecciona la hoja a procesar:",
                        hojas_disponibles,
                        help="Elige la hoja que contiene los datos del catálogo"
                    )
                
                with col2:
                    # Mostrar vista previa de hojas
                    st.markdown("**Hojas disponibles:**")
                    for i, hoja in enumerate(hojas_disponibles):
                        try:
                            # Leer solo unas pocas filas para mostrar info
                            df_preview = pd.read_excel(uploaded_file, sheet_name=hoja, nrows=5)
                            filas_totales = len(pd.read_excel(uploaded_file, sheet_name=hoja))
                            st.write(f"📄 {hoja}: {filas_totales} filas, {len(df_preview.columns)} columnas")
                        except:
                            st.write(f"📄 {hoja}: No se pudo leer")
                
                # Configuración adicional
                st.subheader("⚙️ Configuración de Carga")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    fila_encabezados = st.number_input(
                        "📍 Fila de encabezados (0-indexado):",
                        min_value=0,
                        max_value=20,
                        value=0,
                        help="Fila donde están los nombres de las columnas"
                    )
                
                with col2:
                    saltar_filas = st.number_input(
                        "⏭️ Filas a saltar al inicio:",
                        min_value=0,
                        max_value=50,
                        value=0,
                        help="Número de filas vacías o de título a saltar"
                    )
                
                with col3:
                    auto_detectar = st.checkbox(
                        "🔍 Auto-detectar encabezados",
                        value=True,
                        help="Intentar detectar automáticamente la fila de encabezados"
                    )
                
                # Botón para procesar la hoja seleccionada
                if st.button("📊 Procesar Hoja Seleccionada", type="primary"):
                    with st.spinner(f"🔄 Procesando hoja '{hoja_seleccionada}'..."):
                        
                        # Auto-detectar fila de encabezados si está activado
                        if auto_detectar:
                            fila_detectada = detectar_fila_encabezados_excel(uploaded_file, hoja_seleccionada)
                            if fila_detectada != fila_encabezados:
                                st.info(f"🔍 Auto-detectado: fila de encabezados en posición {fila_detectada}")
                                fila_encabezados = fila_detectada
                        
                        # Cargar los datos con la configuración especificada
                        df = pd.read_excel(
                            uploaded_file, 
                            sheet_name=hoja_seleccionada,
                            header=fila_encabezados,
                            skiprows=saltar_filas if saltar_filas > fila_encabezados else None
                        )
                        
                        # Limpiar datos
                        df = limpiar_dataframe_proveedor(df)
                        
                        if len(df) == 0:
                            st.error("❌ No hay datos válidos en la hoja seleccionada")
                            return None
                        
                        st.success(f"✅ Hoja '{hoja_seleccionada}' cargada: {len(df):,} filas válidas")
                        
                        # Mostrar vista previa de los datos procesados
                        st.subheader("👀 Vista Previa de Datos Procesados")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Guardar temporalmente para permitir configuración
                        st.session_state['df_proveedor_temp'] = df
                        st.session_state['hoja_procesada'] = hoja_seleccionada
                        
                        return df
                
                # Si ya hay datos temporales, mostrarlos
                if 'df_proveedor_temp' in st.session_state:
                    return st.session_state['df_proveedor_temp']
                
                return None
                
            except Exception as e:
                st.error(f"❌ Error al leer archivo Excel: {str(e)}")
                return None
        
    except Exception as e:
        st.error(f"❌ Error al cargar catálogo: {str(e)}")
        return None

def detectar_fila_encabezados_excel(uploaded_file, sheet_name):
    """Detecta automáticamente la fila de encabezados en Excel"""
    try:
        # Leer las primeras 20 filas sin encabezados
        df_temp = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None, nrows=20)
        
        # Palabras clave que suelen estar en encabezados
        keywords_encabezados = [
            'style', 'sku', 'codigo', 'code', 'precio', 'price', 'cost', 'color',
            'talla', 'size', 'descripcion', 'description', 'stock', 'cantidad',
            'categoria', 'category', 'delivery', 'msrp', 'whsl', 'wholesale'
        ]
        
        for idx, row in df_temp.iterrows():
            # Convertir la fila a string y contar coincidencias
            row_str = ' '.join([str(v).lower() for v in row if pd.notna(v)])
            
            coincidencias = sum(1 for keyword in keywords_encabezados if keyword in row_str)
            
            # Si encontramos 3 o más palabras clave, probablemente es la fila de encabezados
            if coincidencias >= 3:
                return idx
        
        # Si no se detecta, devolver 0
        return 0
        
    except:
        return 0

def limpiar_dataframe_proveedor(df):
    """Limpia el DataFrame del proveedor eliminando filas y columnas vacías"""
    # Hacer una copia para no modificar el original
    df_limpio = df.copy()
    
    # Eliminar filas completamente vacías
    df_limpio = df_limpio.dropna(how='all')
    
    # Eliminar columnas completamente vacías
    df_limpio = df_limpio.dropna(axis=1, how='all')
    
    # Eliminar filas donde todas las columnas importantes están vacías
    # (mantenemos filas que tienen al menos un valor no nulo en columnas de texto)
    columnas_texto = df_limpio.select_dtypes(include=['object']).columns
    if len(columnas_texto) > 0:
        # Mantener filas que tienen al menos un valor de texto no vacío
        mask_texto = df_limpio[columnas_texto].notna().any(axis=1)
        df_limpio = df_limpio[mask_texto]
    
    # Limpiar espacios en blanco en columnas de texto
    for col in df_limpio.select_dtypes(include=['object']).columns:
        df_limpio[col] = df_limpio[col].astype(str).str.strip()
        # Reemplazar strings vacíos con NaN
        df_limpio[col] = df_limpio[col].replace(['', 'nan', 'NaN', 'None'], np.nan)
    
    # Eliminar filas donde el primer 30% de las columnas están todas vacías
    # (esto ayuda a eliminar filas separadoras o de título)
    num_cols_importantes = max(1, len(df_limpio.columns) // 3)
    cols_importantes = df_limpio.columns[:num_cols_importantes]
    mask_validas = df_limpio[cols_importantes].notna().any(axis=1)
    df_limpio = df_limpio[mask_validas]
    
    # Reset del índice
    df_limpio = df_limpio.reset_index(drop=True)
    
    return df_limpio

def configurar_mapeo_columnas(df_proveedor, marca):
    """Configura el mapeo de columnas del proveedor"""
    st.subheader("🔧 Configuración de Columnas")
    
    # Mostrar información sobre el DataFrame procesado
    if 'hoja_procesada' in st.session_state:
        st.info(f"📋 Procesando hoja: **{st.session_state['hoja_procesada']}** ({len(df_proveedor)} filas válidas)")
    
    # Información sobre columnas detectadas
    with st.expander("ℹ️ Información de Columnas Detectadas", expanded=False):
        st.write("**Columnas disponibles en tu archivo:**")
        for i, col in enumerate(df_proveedor.columns):
            # Mostrar muestra de datos no nulos para cada columna
            datos_muestra = df_proveedor[col].dropna().head(3).tolist()
            muestra_str = ", ".join([str(x)[:30] for x in datos_muestra]) if datos_muestra else "Sin datos"
            st.write(f"- **{col}**: {muestra_str}")
        
        # Ayuda específica para True Religion
        st.markdown("---")
        st.markdown("**💡 Guía para archivos True Religion:**")
        st.write("- **SKU**: Usa 'STYLE-COLOR' (SKU completo) o 'STYLE' (SKU base)")
        st.write("- **Color**: Usa 'CODE COLOR' (códigos de color como 1001, 1700)")
        st.write("- **Descripción**: Usa 'STYLE DESCRIPTION'")
        st.write("- **Precio**: Busca columnas como 'MSRP', 'WHSL', 'MEXICO WHSL'")
        st.write("- **Talla**: Usa 'SIZING' si está disponible")
    
    columnas_disponibles = [""] + list(df_proveedor.columns)
    
    # Detección automática mejorada
    mapeo_auto = detectar_columnas_automaticamente(df_proveedor.columns)
    
    st.markdown("#### 🎯 Mapeo de Columnas")
    st.info("💡 **Nota**: Solo el SKU es obligatorio. Las demás columnas son opcionales.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        col_sku = st.selectbox(
            "📦 Columna SKU/Código *", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('sku')),
            help="Identificador único del producto (obligatorio)"
        )
        
        col_precio = st.selectbox(
            "💰 Columna Precio", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('precio')),
            help="Precio de compra o wholesale (opcional)"
        )
        
        col_categoria = st.selectbox(
            "📂 Columna Categoría", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('categoria')),
            help="Tipo o categoría del producto"
        )
    
    with col2:
        col_descripcion = st.selectbox(
            "📝 Columna Descripción", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('descripcion')),
            help="Nombre o descripción del producto"
        )
        
        col_stock = st.selectbox(
            "📊 Columna Stock", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('stock')),
            help="Cantidad disponible en inventario"
        )
        
        col_talla = st.selectbox(
            "📏 Columna Talla", 
            columnas_disponibles,
            index=get_index_safe(columnas_disponibles, mapeo_auto.get('talla')),
            help="Talla o tamaño del producto"
        )
    
    col_color = st.selectbox(
        "🎨 Columna Color", 
        columnas_disponibles,
        index=get_index_safe(columnas_disponibles, mapeo_auto.get('color')),
        help="Color del producto"
    )
    
    # Vista previa del mapeo
    if col_sku:
        st.subheader("👀 Vista Previa del Mapeo")
        
        # Crear DataFrame de muestra con el mapeo
        columnas_mapeadas = {}
        if col_sku: columnas_mapeadas['SKU'] = col_sku
        if col_precio and col_precio != "": columnas_mapeadas['Precio'] = col_precio
        if col_categoria: columnas_mapeadas['Categoría'] = col_categoria
        if col_descripcion: columnas_mapeadas['Descripción'] = col_descripcion
        if col_stock: columnas_mapeadas['Stock'] = col_stock
        if col_talla: columnas_mapeadas['Talla'] = col_talla
        if col_color: columnas_mapeadas['Color'] = col_color
        
        # Mostrar muestra de datos mapeados
        columnas_existentes = [col for col in columnas_mapeadas.values() if col in df_proveedor.columns]
        if columnas_existentes:
            df_muestra = df_proveedor[columnas_existentes].head(5)
            df_muestra.columns = [k for k, v in columnas_mapeadas.items() if v in columnas_existentes]
            st.dataframe(df_muestra, use_container_width=True)
        
        # Estadísticas del mapeo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Contar filas con SKU válido
            filas_sku_validas = df_proveedor[col_sku].notna().sum()
            st.metric("Filas con SKU", f"{filas_sku_validas:,}")
        
        with col2:
            # Contar filas con precio válido si existe
            if col_precio and col_precio != "":
                precios_validos = pd.to_numeric(df_proveedor[col_precio], errors='coerce').notna().sum()
                st.metric("Filas con Precio", f"{precios_validos:,}")
            else:
                st.metric("Filas con Precio", "N/A")
        
        with col3:
            # Filas válidas con SKU
            st.metric("Filas Válidas", f"{filas_sku_validas:,}")
    
    # Procesar datos del proveedor
    if st.button("🔄 Procesar Catálogo del Proveedor", type="primary"):
        if not col_sku:
            st.error("❌ La columna SKU es obligatoria")
            return
        
        with st.spinner("🔄 Procesando datos del proveedor..."):
            try:
                df_procesado = procesar_datos_proveedor(
                    df_proveedor, col_sku, col_precio, col_categoria,
                    col_descripcion, col_stock, col_talla, col_color, marca
                )
                
                if df_procesado is not None and len(df_procesado) > 0:
                    st.session_state['df_proveedor'] = df_procesado
                    
                    # Limpiar datos temporales
                    if 'df_proveedor_temp' in st.session_state:
                        del st.session_state['df_proveedor_temp']
                    if 'hoja_procesada' in st.session_state:
                        del st.session_state['hoja_procesada']
                    
                    st.success(f"✅ Catálogo procesado: {len(df_procesado):,} productos válidos")
                    
                    # Mostrar estadísticas del proveedor
                    mostrar_estadisticas_proveedor(df_procesado)
                    
                    # Botón para continuar
                    if st.button("➡️ Continuar a Selección de Productos", type="primary"):
                        st.rerun()
                else:
                    st.error("❌ No se pudieron procesar los datos del proveedor. Verifica el mapeo de columnas.")
                    
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")

def detectar_columnas_automaticamente(columnas):
    """Detecta automáticamente las columnas del proveedor con patrones mejorados"""
    mapeo = {}
    columnas_lower = [col.lower().strip().replace('-', '').replace('_', '') for col in columnas]
    
    # Patrones específicos para True Religion y proveedores similares
    patrones = {
        'sku': [
            'stylecolor', 'style color', 'sku', 'codigo', 'code', 'item', 'parte', 'product_id',
            'style', 'modelo'  # STYLE puede ser SKU base
        ],
        'precio': [
            'precio', 'price', 'cost', 'costo', 'valor', 'amount', 'wholesale',
            'whsl', 'mexico whsl', 'mx whsl', 'cost price', 'unit cost',
            'msrp', 'retail'  # Precios reales, NO code color
        ],
        'descripcion': [
            'descripcion', 'description', 'desc', 'product', 'nombre', 'name',
            'style description', 'product name', 'item description'
        ],
        'categoria': [
            'categoria', 'category', 'tipo', 'type', 'class', 'classification',
            'product category', 'item type', 'gender', 'genero'
        ],
        'stock': [
            'stock', 'cantidad', 'qty', 'inventory', 'disponible', 'available',
            'units', 'quantity', 'inv', 'on hand', 'sizing'  # A veces SIZING es stock
        ],
        'talla': [
            'talla', 'size', 'medida', 'dimension', 'sizing',
            'size range', 'fit', 'measurement'
        ],
        'color': [
            'codecolor', 'code color', 'colorcode', 'color code',  # Para True Religion
            'color', 'colour', 'tone', 'shade', 'color description',
            'colour description', 'fabric color'
        ]
    }
    
    # Mapeo manual para casos específicos de True Religion
    for i, col in enumerate(columnas):
        col_clean = col.strip().upper().replace('-', '').replace('_', '')
        
        # Mapeo específico para True Religion
        if col_clean == 'STYLECOLOR' or col_clean == 'STYLE-COLOR':
            mapeo['sku'] = col
        elif col_clean == 'STYLE' and 'sku' not in mapeo:
            mapeo['sku'] = col  # STYLE como SKU base si no hay STYLE-COLOR
        elif col_clean == 'CODECOLOR' or col_clean == 'CODE COLOR':
            mapeo['color'] = col
        elif col_clean == 'STYLEDESCRIPTION' or col_clean == 'STYLE DESCRIPTION':
            mapeo['descripcion'] = col
        elif col_clean == 'COLORDESCRIPTION' or col_clean == 'COLOR DESCRIPTION':
            mapeo['descripcion'] = col  # Descripción de color como descripción
        elif col_clean == 'SIZING':
            mapeo['talla'] = col
        elif col_clean in ['MSRP', 'WHSL', 'PRICE', 'WHOLESALE', 'MEXICOWHSL', 'MEXICO WHSL']:
            mapeo['precio'] = col
    
    # Si no encontró con mapeo manual, usar patrones generales
    if not mapeo:
        for tipo, keywords in patrones.items():
            encontrado = False
            for i, col_lower in enumerate(columnas_lower):
                for keyword in keywords:
                    if keyword == col_lower or keyword in col_lower:
                        mapeo[tipo] = columnas[i]
                        encontrado = True
                        break
                if encontrado:
                    break
    
    return mapeo

def get_index_safe(lista, valor):
    """Obtiene el índice de manera segura"""
    try:
        return lista.index(valor) if valor and valor in lista else 0
    except:
        return 0

def procesar_datos_proveedor(df, col_sku, col_precio, col_categoria, 
                           col_descripcion, col_stock, col_talla, col_color, marca):
    """Procesa los datos del proveedor"""
    try:
        df_procesado = df.copy()
        
        # Mapear columnas (solo SKU es obligatorio)
        mapeo = {'SKU_Proveedor': col_sku}
        
        if col_precio and col_precio != "": 
            mapeo['Precio_Proveedor'] = col_precio
        if col_categoria: 
            mapeo['Categoria_Proveedor'] = col_categoria
        if col_descripcion: 
            mapeo['Descripcion'] = col_descripcion
        if col_stock: 
            mapeo['Stock_Disponible'] = col_stock
        if col_talla: 
            mapeo['Talla_Proveedor'] = col_talla
        if col_color: 
            mapeo['Color_Proveedor'] = col_color
        
        # Renombrar columnas
        df_procesado = df_procesado.rename(columns={v: k for k, v in mapeo.items()})
        
        # Agregar marca
        df_procesado['Marca'] = marca
        
        # Limpiar datos numéricos (solo si existen)
        if 'Precio_Proveedor' in df_procesado.columns:
            df_procesado['Precio_Proveedor'] = pd.to_numeric(df_procesado['Precio_Proveedor'], errors='coerce')
            df_procesado['Precio_Proveedor'] = df_procesado['Precio_Proveedor'].fillna(0)
        else:
            df_procesado['Precio_Proveedor'] = 0.0
            
        if 'Stock_Disponible' in df_procesado.columns:
            df_procesado['Stock_Disponible'] = pd.to_numeric(df_procesado['Stock_Disponible'], errors='coerce')
            df_procesado['Stock_Disponible'] = df_procesado['Stock_Disponible'].fillna(0)
        else:
            df_procesado['Stock_Disponible'] = 0
        
        # Procesar categoría
        if 'Categoria_Proveedor' in df_procesado.columns:
            df_procesado['Categoria'] = df_procesado['Categoria_Proveedor'].apply(limpiar_categoria)
        elif 'Descripcion' in df_procesado.columns:
            df_procesado['Categoria'] = df_procesado['Descripcion'].apply(limpiar_categoria)
        else:
            df_procesado['Categoria'] = 'Sin Categoría'
        
        # Extraer información del SKU
        if 'SKU_Proveedor' in df_procesado.columns:
            # Extraer modelo
            df_procesado['modelo'] = df_procesado['SKU_Proveedor'].apply(extraer_modelo_sku)
            
            # Extraer talla y color del SKU si no están disponibles
            extraidos = df_procesado['SKU_Proveedor'].apply(extraer_color_talla_sku)
            
            if 'Talla_Proveedor' not in df_procesado.columns:
                df_procesado['talla'] = extraidos.apply(lambda d: d.get('talla'))
            else:
                df_procesado['talla'] = df_procesado['Talla_Proveedor'].fillna(
                    extraidos.apply(lambda d: d.get('talla'))
                )
            
            if 'Color_Proveedor' not in df_procesado.columns:
                df_procesado['color'] = extraidos.apply(lambda d: d.get('color'))
            else:
                df_procesado['color'] = df_procesado['Color_Proveedor'].fillna(
                    extraidos.apply(lambda d: d.get('color'))
                )

        # Normalizar tallas para comparación
        if 'talla' in df_procesado.columns:
            df_procesado['talla_normalizada'] = df_procesado['talla'].apply(normalizar_talla)
        else:
            df_procesado['talla_normalizada'] = None

        # Filtrar productos válidos (solo SKU es obligatorio)
        df_procesado = df_procesado.dropna(subset=['SKU_Proveedor'])
        df_procesado = df_procesado[df_procesado['SKU_Proveedor'].astype(str).str.strip() != '']
        
        return df_procesado
        
    except Exception as e:
        st.error(f"❌ Error procesando datos: {str(e)}")
        return None

def mostrar_estadisticas_proveedor(df_proveedor):
    """Muestra estadísticas del catálogo del proveedor"""
    st.subheader("📊 Estadísticas del Catálogo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Productos", f"{len(df_proveedor):,}")
    
    with col2:
        if 'Categoria' in df_proveedor.columns:
            st.metric("Categorías", df_proveedor['Categoria'].nunique())
    
    with col3:
        if 'Stock_Disponible' in df_proveedor.columns and df_proveedor['Stock_Disponible'].sum() > 0:
            stock_total = df_proveedor['Stock_Disponible'].sum()
            st.metric("Stock Total", f"{stock_total:,.0f}")
        else:
            st.metric("Stock Total", "No disponible")
    
    with col4:
        if 'Precio_Proveedor' in df_proveedor.columns and df_proveedor['Precio_Proveedor'].sum() > 0:
            precio_promedio = df_proveedor[df_proveedor['Precio_Proveedor'] > 0]['Precio_Proveedor'].mean()
            st.metric("Precio Promedio", f"${precio_promedio:,.2f}")
        else:
            st.metric("Precio Promedio", "No disponible")
    
    # Top categorías del proveedor
    if 'Categoria' in df_proveedor.columns:
        st.subheader("🏆 Top Categorías del Proveedor")
        cat_dist = df_proveedor['Categoria'].value_counts().head(10)
        
        fig_cat_prov = px.bar(
            x=cat_dist.values,
            y=cat_dist.index,
            orientation='h',
            title="Productos por Categoría",
            color=cat_dist.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_cat_prov, use_container_width=True)

# =====================================================
# PASO 4: SELECCIÓN MANUAL - VERSION MEJORADA
# =====================================================

def mostrar_paso_4_seleccion_manual():
    """Paso 4: Selección manual con opciones mejoradas para resolver problemas de matching"""
    st.header("4️⃣ Selección Manual de Productos")
    
    # Verificar que tenemos todo lo necesario
    predicciones = st.session_state.get('predicciones')
    distribucion = st.session_state.get('distribucion_demanda')
    df_proveedor = st.session_state.get('df_proveedor')
    
    if not all([predicciones, distribucion is not None, df_proveedor is not None]):
        st.error("❌ Faltan datos. Completa los pasos anteriores.")
        return
    
    # Configuración del matching MEJORADA
    st.subheader("⚙️ Configuración del Matching - VERSIÓN MEJORADA")
    
    # Alerta sobre las mejoras
    st.info("🚀 **Nuevas funciones**: Sistema mejorado para resolver problemas de comas en códigos y tallas incompatibles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metodo_matching = st.selectbox(
            "🎯 Método de Matching",
            ["Híbrido Inteligente", "Solo SKU Exacto", "Solo Atributos"]
        )
        
        umbral_similitud = st.slider("📊 Umbral de similitud (%)", 50, 100, 65)  # Reducido por defecto
        
        # NUEVA OPCIÓN: Ignorar tallas
        ignorar_tallas = st.checkbox(
            "👔 Asumir que todas las tallas están disponibles", 
            value=True,
            help="Si está activado, no penaliza por diferencias de talla (RECOMENDADO para solucionar problemas de tallas)"
        )
    
    with col2:
        mostrar_solo_disponibles = st.checkbox("📦 Solo productos con stock", value=False)
        
        incluir_similares = st.checkbox("🔍 Incluir productos similares", value=True)
        
        # NUEVA OPCIÓN: Ignorar comas
        limpiar_codigos = st.checkbox(
            "🧹 Limpiar comas y caracteres especiales", 
            value=True,
            help="Remueve comas, puntos y espacios de códigos para mejor matching (SOLUCIONA el problema 1,001 vs 1001)"
        )
    
    # Mostrar configuración actual
    with st.expander("ℹ️ Configuración Activa", expanded=False):
        st.write("**Configuración optimizada para resolver problemas comunes:**")
        st.write(f"• Umbral reducido: {umbral_similitud}% (más permisivo)")
        st.write(f"• Ignorar tallas: {'✅ ACTIVADO' if ignorar_tallas else '❌ Desactivado'}")
        st.write(f"• Limpiar códigos: {'✅ ACTIVADO' if limpiar_codigos else '❌ Desactivado'}")
        st.write(f"• Incluir similares: {'✅ ACTIVADO' if incluir_similares else '❌ Desactivado'}")
    
    # Generar matching de opciones
    if st.button("🔍 Buscar Opciones Disponibles", type="primary"):
        with st.spinner("🤖 Buscando opciones con algoritmo mejorado..."):
            
            # Configuración del matching MEJORADA
            config_matching = {
                'metodo': metodo_matching,
                'umbral_similitud': umbral_similitud,
                'mostrar_solo_disponibles': mostrar_solo_disponibles,
                'incluir_similares': incluir_similares,
                'ignorar_tallas': ignorar_tallas,        # NUEVO
                'limpiar_codigos': limpiar_codigos       # NUEVO
            }
            
            # Ejecutar matching de opciones MEJORADO
            opciones_disponibles = ejecutar_matching_opciones_mejorado(
                distribucion, df_proveedor, config_matching
            )
            
            if opciones_disponibles is not None and len(opciones_disponibles) > 0:
                st.session_state['opciones_disponibles'] = opciones_disponibles
                st.session_state['config_matching'] = config_matching  # Guardar config
                st.success(f"✅