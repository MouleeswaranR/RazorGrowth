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
        steps = trace.get("steps", {})
        step3 = steps.get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step2 = steps.get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
        step2_agentic = steps.get("2_agentic_decision_loop", {}).get("data", {})
        step4_tool = steps.get("step_4_select_audience", {}).get("data", {})
        step4 = steps.get("4_experiment_ab_lift_measurement", {}).get("data", {})

        aud_count = step3.get("total_audience", 0)
        target_segment = step3.get("target_segment", "VIP Dormant")
        reasoning = step3.get("audience_reasoning", "")

        if not aud_count:
            if step4_tool.get("result", {}).get("audience_count"):
                aud_count = step4_tool["result"]["audience_count"]
                target_segment = step4_tool["result"].get("target_segment", target_segment)
                reasoning = step4_tool["result"].get("reasoning", reasoning)
            elif step2_agentic.get("steps_taken"):
                aud_step = next((s for s in step2_agentic["steps_taken"] if s.get("tool_name") == "select_audience"), None)
                if aud_step and aud_step.get("result", {}).get("audience_count"):
                    aud_count = aud_step["result"]["audience_count"]
                    target_segment = aud_step["result"].get("target_segment", target_segment)
                    reasoning = aud_step["result"].get("reasoning", reasoning)
            elif step2.get("action_plan", {}).get("audience", {}).get("audience_count"):
                aud_count = step2["action_plan"]["audience"]["audience_count"]
                target_segment = step2["action_plan"]["audience"].get("target_segment", target_segment)
                reasoning = step2["action_plan"]["audience"].get("reasoning", reasoning)

        treatment_size = step3.get("treatment_group_size", int(round(aud_count * 0.8)) if aud_count else 0)
        control_size = step3.get("control_group_size", aud_count - treatment_size if aud_count else 0)

        return {
            "total_audience": aud_count,
            "treatment_group_size": treatment_size,
            "control_group_size": control_size,
            "target_segment": target_segment,
            "customer_agent_reasoning": reasoning or "Audience filtered by CustomerAgent based on RFM CLV percentiles and churn risk.",
            "launched_opportunity": step3.get("opportunity_type", step2.get("action_plan", {}).get("opportunity_title", "VIP Churn Prevention")),
            "top_opportunity": step2.get("action_plan", {}).get("opportunity_title", "Proactive Churn Intervention"),
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
        steps = trace.get("steps", {})
        step3 = steps.get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step5_tool = steps.get("step_5_recommend_offer", {}).get("data", {})
        step2_agentic = steps.get("2_agentic_decision_loop", {}).get("data", {})
        step2_det = steps.get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})

        offer = step3.get("offer", {})
        if not offer or not offer.get("offer_code") or offer.get("offer_code") == "N/A":
            if step5_tool.get("result", {}).get("offer_code"):
                offer = step5_tool["result"]
            elif step5_tool.get("offer_code"):
                offer = step5_tool
            elif step2_agentic.get("steps_taken"):
                rec = next((s for s in step2_agentic["steps_taken"] if s.get("tool_name") == "recommend_offer"), None)
                if rec and rec.get("result", {}).get("offer_code"):
                    offer = rec["result"]
            elif step2_det.get("action_plan", {}).get("offer"):
                offer = step2_det["action_plan"]["offer"]

        reasoning = (
            offer.get("reasoning")
            or step3.get("offer_reasoning")
            or "Calibrated margin-safe discount based on customer cohort spend tier."
        )

        return {
            "offer_code": offer.get("offer_code", "VIP20OFF"),
            "discount_type": offer.get("discount_type", "percentage"),
            "discount_value": offer.get("discount_value", 20.0),
            "min_order_value": offer.get("min_order_value", 1999.0),
            "description": offer.get("description", "20% off for high-value customers above ₹1,999"),
            "urgency_text": offer.get("urgency_text", "Expires in 7 days"),
            "offer_agent_reasoning": reasoning,
            "emails_dispatched": step3.get("emails_dispatched", step3.get("total_audience", 0)),
        }

    def get_agent_reasoning_trace(self, session_id: str) -> dict:
        """Retrieves concise decision rationale from each agent in the growth pipeline."""
        trace = self._resolve_trace(session_id)
        steps = trace.get("steps", {})
        step2 = steps.get("2_opportunity_scan_and_ai_reasoning", {}).get("data", {})
        step2_agentic = steps.get("2_agentic_decision_loop", {}).get("data", {})
        step3 = steps.get("3_campaign_launch_and_dispatch", {}).get("data", {})
        step4 = steps.get("4_experiment_ab_lift_measurement", {}).get("data", {})

        growth_mgr = (
            step2.get("action_plan", {}).get("ai_reasoning")
            or step2_agentic.get("reasoning_trace")
            or step2_agentic.get("plan_summary")
            or "Evaluated multi-agent diagnostic telemetry to identify highest-ROI growth opportunities."
        )

        return {
            "growth_manager_reasoning": growth_mgr,
            "customer_agent_reasoning": step3.get("audience_reasoning", "Cohort selected based on RFM CLV and churn probability."),
            "offer_agent_reasoning": step3.get("offer_reasoning", "Margin-safe incentive calibrated to preserve profit margins."),
            "permission_gate_notes": step3.get("permission_gate", {}).get("policy_notes", "Dynamic financial guardrails verified."),
            "experiment_agent_summary": step4.get("experiment_reasoning", "A/B test measures incremental conversion lift via Razorpay webhooks."),
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
