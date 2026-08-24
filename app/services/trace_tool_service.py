from app.services.trace_logger_service import trace_logger_service


class TraceToolService:
    """Provides targeted micro-tools for chatbot retrieval, reducing context window consumption."""

    def _resolve_trace(self, session_id: str) -> dict:
        """Finds session trace strictly by session_id; only falls back to latest recorded trace if session_id is None."""
        if session_id:
            return trace_logger_service.get_session_trace(session_id) or {}
        return trace_logger_service.get_latest_trace() or {}

    def get_audience_breakdown(self, session_id: str) -> dict:
        """Retrieves audience size, segmentation criteria, and CustomerAgent reasoning."""
        trace = self._resolve_trace(session_id)
        step3 = trace.get("steps", {}).get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step2 = trace.get("steps", {}).get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
        step4 = trace.get("steps", {}).get("4_experiment_ab_lift_measurement", {}).get("data", {})

        return {
            "total_audience": step3.get("total_audience", 0),
            "treatment_group_size": step3.get("treatment_group_size", 0),
            "control_group_size": step3.get("control_group_size", 0),
            "target_segment": step3.get("target_segment", "N/A"),
            "customer_agent_reasoning": step3.get("audience_reasoning", "Audience filtered based on CLV and churn risk."),
            "launched_opportunity": step3.get("opportunity_type", step2.get("action_plan", {}).get("opportunity_title", "N/A")),
            "top_opportunity": step2.get("action_plan", {}).get("opportunity_title", "N/A"),
            "conversions_recorded": step4.get("metrics", {}).get("treatment_orders_count", 0),
        }

    def get_experiment_lift_summary(self, session_id: str) -> dict:
        """Retrieves statistical A/B test metrics, lift percentages, converted customers, and net incremental GMV."""
        trace = self._resolve_trace(session_id)
        step4 = trace.get("steps", {}).get("4_experiment_ab_lift_measurement", {}).get("data", {})
        step3 = trace.get("steps", {}).get("3_campaign_launch_and_dispatch", {}).get("data", {})
        metrics = step4.get("metrics", {})

        treatment_orders = metrics.get("treatment_orders_count", 0)
        control_orders = metrics.get("control_orders_count", 0)
        treatment_total = step3.get("treatment_group_size", metrics.get("treatment_total_count", 0))
        control_total = step3.get("control_group_size", metrics.get("control_total_count", 0))
        captured_gmv = step4.get("captured_gmv", metrics.get("incremental_revenue_inr", 0.0))
        incremental_gmv = metrics.get("incremental_revenue_inr", 0.0)

        if step4:
            status = (
                f"Live A/B experiment measured via Razorpay Webhooks. {treatment_orders} treatment conversion(s) recorded."
                if treatment_orders > 0
                else "Experiment active with Razorpay Test Orders created. Awaiting webhook payment events."
            )
        else:
            status = "No experiment launched yet in this session."

        return {
            "opportunity_title": step3.get("opportunity_type", "Targeted Campaign"),
            "treatment_conversions": treatment_orders,
            "treatment_total": treatment_total,
            "treatment_conversion_rate": f"{metrics.get('treatment_conversion_rate', 0.0) * 100:.2f}%",
            "control_conversions": control_orders,
            "control_total": control_total,
            "control_conversion_rate": f"{metrics.get('control_conversion_rate', 0.0) * 100:.2f}%",
            "relative_conversion_lift": metrics.get("relative_lift_display", "N/A (control = 0%)"),
            "absolute_difference": f"{metrics.get('absolute_difference_percentage', 0.0):+0.2f} pp",
            "incremental_orders": metrics.get("incremental_orders_count", treatment_orders),
            "captured_gmv_inr": f"₹{captured_gmv:,.2f}",
            "incremental_gmv_inr": f"₹{incremental_gmv:,.2f}",
            "status_summary": status,
        }

    def get_campaign_offer_details(self, session_id: str) -> dict:
        """Retrieves incentive terms, coupon codes, and messaging copy rationale."""
        trace = self._resolve_trace(session_id)
        step3 = trace.get("steps", {}).get("3_campaign_launch_and_dispatch", {}).get("data", {})
        offer = step3.get("offer", {})

        return {
            "offer_code": offer.get("offer_code", "N/A"),
            "discount_type": offer.get("discount_type", "N/A"),
            "discount_value": offer.get("discount_value", 0.0),
            "description": offer.get("description", "N/A"),
            "offer_agent_reasoning": step3.get("offer_reasoning", "Incentive calibrated for margin preservation."),
            "emails_dispatched": step3.get("emails_dispatched", 0),
        }

    def get_agent_reasoning_trace(self, session_id: str) -> dict:
        """Retrieves concise decision rationale from each agent in the growth pipeline."""
        trace = self._resolve_trace(session_id)
        steps = trace.get("steps", {})
        step2 = steps.get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
        step3 = steps.get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step4 = steps.get("4_experiment_ab_lift_measurement", {}).get("data", {})

        return {
            "growth_manager_reasoning": step2.get("action_plan", {}).get("ai_reasoning", "Identified primary revenue leak."),
            "customer_agent_reasoning": step3.get("audience_reasoning", "Cohort selected based on RFM profile."),
            "offer_agent_reasoning": step3.get("offer_reasoning", "Margin-safe incentive selected."),
            "permission_gate_notes": step3.get("permission_gate", {}).get("policy_notes", "Dynamic guardrails evaluated."),
            "experiment_agent_summary": step4.get("experiment_reasoning", "A/B test measured conversion lift."),
        }

    def get_targeted_customer_list(self, session_id: str) -> dict:
        """Pulls the structured target customer cohort (names, emails, segments, spend) from the growth plan trace."""
        trace = self._resolve_trace(session_id)
        step2 = trace.get("steps", {}).get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
        step3 = trace.get("steps", {}).get("3_campaign_launch_and_dispatch", {}).get("data", {})

        audience = step2.get("action_plan", {}).get("audience", {})
        target_customers = audience.get("target_customers", []) or step3.get("target_customers", [])

        return {
            "total_targeted": len(target_customers) or step3.get("total_audience", 0),
            "target_segment": audience.get("target_segment", step3.get("target_segment", "N/A")),
            "reasoning": audience.get("reasoning", step3.get("audience_reasoning", "Targeted cohort based on CLV and churn risk.")),
            "targeted_customers": [
                {
                    "customer_id": c.get("customer_id") or c.get("id"),
                    "name": c.get("name"),
                    "email": c.get("email"),
                    "favorite_category": c.get("favorite_category"),
                    "segment": c.get("segment"),
                    "total_spend": c.get("total_spend"),
                }
                for c in target_customers
            ],
        }

    def get_converted_customer_details(self, session_id: str) -> dict:
        """Retrieves exact customer names, order IDs, and payment amounts for converted campaign orders."""
        trace = self._resolve_trace(session_id)
        step4 = trace.get("steps", {}).get("4_experiment_ab_lift_measurement", {}).get("data", {})
        step3 = trace.get("steps", {}).get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step2 = trace.get("steps", {}).get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})

        converted = step4.get("converted_customers", [])
        captured_gmv = step4.get("captured_gmv", 0.0)
        incremental_gmv = step4.get("metrics", {}).get("incremental_revenue_inr", 0.0)

        return {
            "total_conversions": len(converted),
            "opportunity_title": step3.get("opportunity_type", step2.get("action_plan", {}).get("opportunity_title", "Growth Campaign")),
            "converted_customers": converted,
            "captured_gmv_inr": f"₹{captured_gmv:,.2f}",
            "incremental_gmv_inr": f"₹{incremental_gmv:,.2f}",
            "status_note": (
                f"{len(converted)} customer conversion(s) verified via Razorpay Webhooks."
                if converted
                else "No customer conversions recorded yet for this session."
            ),
        }

    def route_and_fetch_relevant_context(self, query: str, session_id: str) -> dict:
        """Selects and returns only the relevant tool payload based on merchant query intent."""
        query_lower = query.lower()
        trace = self._resolve_trace(session_id)
        merchant_id = trace.get("merchant_id") or "merch_demo"

        # Specific customer conversion queries (who paid / who accepted / order details)
        if any(w in query_lower for w in ["who accepted", "who paid", "which customer paid", "who bought", "payer", "who converted", "who payed", "order_"]):
            return {
                "tool": "get_converted_customer_details",
                "tools_used": ["get_converted_customer_details", "get_experiment_lift_summary", "get_audience_breakdown"],
                "converted_customer_details": self.get_converted_customer_details(session_id),
                "experiment_metrics": self.get_experiment_lift_summary(session_id),
                "audience_details": self.get_audience_breakdown(session_id),
                "campaign_offer": self.get_campaign_offer_details(session_id),
            }

        # Targeted audience cohort lists (who was targeted / list of users)
        if any(w in query_lower for w in ["who was targeted", "targeted customers", "targeted list", "audience members", "which customers were selected"]):
            return {
                "tool": "get_targeted_customer_list",
                "tools_used": ["get_targeted_customer_list", "get_audience_breakdown"],
                "targeted_customers": self.get_targeted_customer_list(session_id),
                "audience_details": self.get_audience_breakdown(session_id),
            }

        if any(w in query_lower for w in ["offer", "coupon", "code", "discount", "incentive"]):
            return {
                "tool": "get_campaign_offer_details",
                "tools_used": ["get_campaign_offer_details"],
                "data": self.get_campaign_offer_details(session_id),
            }
        if any(w in query_lower for w in ["experiment", "lift", "conversion", "ab", "a/b", "gmv", "result"]):
            return {
                "tool": "get_experiment_lift_summary",
                "tools_used": ["get_experiment_lift_summary"],
                "data": self.get_experiment_lift_summary(session_id),
            }
        if any(w in query_lower for w in ["audience", "count", "users", "customers", "target", "who"]):
            return {
                "tool": "get_audience_breakdown",
                "tools_used": ["get_audience_breakdown"],
                "data": self.get_audience_breakdown(session_id),
            }
        if any(w in query_lower for w in ["reason", "why", "agent", "step", "explain"]):
            return {
                "tool": "get_agent_reasoning_trace",
                "tools_used": ["get_agent_reasoning_trace"],
                "data": self.get_agent_reasoning_trace(session_id),
            }

        # Hybrid Retrieval Fallback: Query semantic vector memory for relevant historical sessions
        from app.services.vector_memory_service import vector_memory_service
        similar_past_memories = vector_memory_service.find_similar_memories(
            merchant_id=merchant_id,
            query_text=query,
            top_k=3,
        )

        return {
            "tool": "hybrid_vector_memory_summary",
            "tools_used": ["hybrid_vector_memory_summary", "vector_memory_search", "get_audience_breakdown", "get_experiment_lift_summary"],
            "historical_similar_campaigns": similar_past_memories,
            "current_session_audience": self.get_audience_breakdown(session_id),
            "current_session_offer": self.get_campaign_offer_details(session_id),
            "current_session_experiment": self.get_experiment_lift_summary(session_id),
        }


trace_tool_service = TraceToolService()
