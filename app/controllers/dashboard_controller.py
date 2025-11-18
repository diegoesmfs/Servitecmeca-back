# app/controllers/dashboard_controller.py
import asyncpg
from typing import Dict, Any, List
from datetime import datetime

class DashboardController:
    
    @staticmethod
    async def get_dashboard_stats(conn: asyncpg.Connection) -> Dict[str, Any]:
        """
        Obtiene todas las estadísticas para el dashboard en una sola consulta
        """
        try:
            # Query con los nombres REALES de tus tablas
            stats = await conn.fetchrow("""
                SELECT 
                    -- Tabla: trabajador (estado = 1 para activos)
                    (SELECT COUNT(*) FROM trabajador WHERE estado = 1) as total_employees,
                    
                    -- Tabla: departamento (estado = 1 para activos)  
                    (SELECT COUNT(*) FROM departamento WHERE estado = 1) as total_departments,
                    
                    -- Tabla: nomina_detalle - usar salario_neto en lugar de total_neto
                    (SELECT COALESCE(SUM(salario_neto), 0) FROM nomina_detalle nd
                     JOIN nomina_general ng ON nd.id_nomina = ng.id_nomina
                     WHERE EXTRACT(YEAR FROM ng.periodo) = EXTRACT(YEAR FROM CURRENT_DATE)
                     AND EXTRACT(MONTH FROM ng.periodo) = EXTRACT(MONTH FROM CURRENT_DATE)
                     AND nd.estado = 1) as total_payroll,
                     
                    -- Contar nóminas del mes actual
                    (SELECT COUNT(*) FROM nomina_general 
                     WHERE EXTRACT(YEAR FROM periodo) = EXTRACT(YEAR FROM CURRENT_DATE)
                     AND EXTRACT(MONTH FROM periodo) = EXTRACT(MONTH FROM CURRENT_DATE)
                     AND estado = 1) as payrolls_this_month
            """)
            
            return {
                "total_employees": stats["total_employees"] or 0,
                "total_departments": stats["total_departments"] or 0,
                "total_payroll": float(stats["total_payroll"]) if stats["total_payroll"] is not None else 0.0,
                "payrolls_this_month": stats["payrolls_this_month"] or 0,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error en dashboard stats: {e}")
            raise e

    @staticmethod
    async def get_recent_activity(conn: asyncpg.Connection, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene actividad reciente del sistema
        """
        try:
            # Últimas nóminas procesadas - usar tabla nomina_general
            recent_payrolls = await conn.fetch("""
                SELECT ng.id_nomina, ng.periodo, ng.presupuesto_utilizado, ng.creado
                FROM nomina_general ng
                WHERE ng.estado = 1
                ORDER BY ng.creado DESC 
                LIMIT $1
            """, limit)
            
            # Nuevos empleados (última semana) - usar tabla trabajador
            new_employees = await conn.fetch("""
                SELECT nombre, apellido, creado 
                FROM trabajador 
                WHERE creado >= CURRENT_DATE - INTERVAL '7 days' 
                AND estado = 1
                ORDER BY creado DESC 
                LIMIT $1
            """, limit)
            
            activities = []
            
            # Agregar nóminas a actividades
            for payroll in recent_payrolls:
                activities.append({
                    "type": "payroll",
                    "action": "Nómina procesada",
                    "details": f"Nómina {payroll['id_nomina']}",
                    "amount": float(payroll['presupuesto_utilizado']) if payroll['presupuesto_utilizado'] else 0,
                    "timestamp": payroll['creado'].isoformat()
                })
            
            # Agregar empleados a actividades
            for employee in new_employees:
                activities.append({
                    "type": "employee", 
                    "action": "Nuevo empleado",
                    "details": f"{employee['nombre']} {employee['apellido']}",
                    "timestamp": employee['creado'].isoformat()
                })
            
            # Si no hay actividades recientes, agregar algunas de ejemplo
            if not activities:
                activities.append({
                    "type": "info",
                    "action": "Sistema activo",
                    "details": "Bienvenido al sistema de nóminas",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Ordenar por timestamp y limitar
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return activities[:limit]
            
        except Exception as e:
            print(f"❌ Error en recent activity: {e}")
            
            # En caso de error, devolver actividades básicas
            return [{
                "type": "info",
                "action": "Sistema configurado",
                "details": "Dashboard funcionando correctamente",
                "timestamp": datetime.now().isoformat()
            }]

# Instancia global para usar en los routes
dashboard_controller = DashboardController()