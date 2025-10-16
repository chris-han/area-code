import streamlit as st
import time
import pandas as pd
import streamlit_shadcn_ui as ui
from datetime import datetime, date, timedelta
import json
import io
from typing import Optional, List, Dict, Any

# Import shared functions following existing patterns
from utils.api_functions import (
    fetch_workflows, render_workflows_table, format_workflow_status,
    handle_refresh_and_fetch, fetch_azure_billing_data, trigger_azure_billing_extract,
    test_azure_connection, fetch_azure_billing_summary, get_azure_subscription_options,
    get_azure_resource_group_options
)
from utils.constants import CONSUMPTION_API_BASE, WORKFLOW_API_BASE
from utils.tooltip_utils import title_with_button, title_with_info_icon
from utils.azure_billing_utils import (
    AzureBillingConfig, CredentialManager, WorkflowParameterManager,
    SecurityUtils, DataRetentionManager
)

def handle_extract_trigger():
    """Handle the extract trigger using current form values or saved configuration"""
    
    # Get current form values from session state (set by render_configuration_form)
    current_enrollment = st.session_state.get("current_enrollment_number", "")
    current_api_key = st.session_state.get("current_api_key", "")
    current_start_date = st.session_state.get("current_start_date")
    current_end_date = st.session_state.get("current_end_date")
    current_batch_size = st.session_state.get("current_batch_size", 1000)
    
    # Try current form values first
    if current_enrollment and current_api_key:
        # Use current form values
        config = AzureBillingConfig(
            enrollment_number=current_enrollment,
            api_key=current_api_key,
            start_date=current_start_date or get_default_start_date(),
            end_date=current_end_date or get_default_end_date(),
            batch_size=current_batch_size
        )
    else:
        # Fall back to saved configuration
        config = WorkflowParameterManager.load_workflow_config()
    
    # Validate we have the required credentials
    if config and config.enrollment_number and config.api_key:
        with st.spinner("Triggering Azure billing extract..."):
            # Use existing status handling pattern
            success = trigger_azure_billing_extract(config.to_dict())
            if success:
                # Log user action for monitoring
                SecurityUtils.log_user_action("azure_billing_extract_triggered", {
                    "start_date": config.start_date.isoformat(),
                    "end_date": config.end_date.isoformat(),
                    "batch_size": config.batch_size,
                    "source": "current_form" if current_enrollment and current_api_key else "saved_config"
                })
                source_msg = " (using current form values)" if current_enrollment and current_api_key else " (using saved configuration)"
                st.session_state["extract_status_msg"] = f"Azure billing extract started successfully{source_msg}!"
                st.session_state["extract_status_type"] = "success"
                st.session_state["extract_status_time"] = time.time()
            else:
                st.session_state["extract_status_msg"] = "Failed to start Azure billing extract"
                st.session_state["extract_status_type"] = "error"
                st.session_state["extract_status_time"] = time.time()
            time.sleep(2)
        st.session_state["refresh_azure_billing"] = True
        st.rerun()
    else:
        # Provide more specific error message
        missing_fields = []
        if not config or not config.enrollment_number:
            missing_fields.append("Enrollment Number")
        if not config or not config.api_key:
            missing_fields.append("API Key")
        
        error_msg = f"Please configure Azure credentials before running extract. Missing: {', '.join(missing_fields)}"
        st.session_state["extract_status_msg"] = error_msg
        st.session_state["extract_status_type"] = "error"
        st.session_state["extract_status_time"] = time.time()

def show():
    """Main Azure billing page function following existing page pattern"""
    
    # Performance monitoring - track page load time
    page_start_time = time.time()
    
    # Clean up old cached data for performance
    DataRetentionManager.cleanup_old_cache()
    
    # Initialize metric counts following existing pattern
    cost_metrics = {"total_cost": 0, "resource_count": 0, "subscription_count": 0, "last_updated": "Never"}
    
    # Header with trigger button following blobs_view pattern
    if title_with_button("Azure Billing", "Run Extract", "trigger_azure_billing_btn", button_size="sm"):
        # Store the trigger flag to handle after form rendering
        st.session_state["trigger_extract"] = True
    
    # Configuration section
    render_configuration_form()
    
    # Handle extract trigger after form is rendered (so we have access to current form values)
    if st.session_state.get("trigger_extract", False):
        st.session_state["trigger_extract"] = False  # Clear the flag
        handle_extract_trigger()
    
    # Fetch data and update metrics following existing pattern
    if "refresh_azure_billing" not in st.session_state:
        st.session_state["refresh_azure_billing"] = False

    if st.session_state.get("refresh_azure_billing", False):
        summary = fetch_azure_billing_summary()
        st.session_state["refresh_azure_billing"] = False
    else:
        summary = fetch_azure_billing_summary()
    
    # Update metrics from summary data
    if summary:
        cost_metrics.update(summary)
    
    # Summary metrics using consistent metric card pattern
    render_summary_metrics(cost_metrics)
    
    # Data table with filters
    render_billing_data_table()
    
    # Workflow status following existing pattern
    st.divider()
    title_with_info_icon("Azure Billing Workflows", "View the status and history of Azure billing processing workflows", "azure_billing_workflows_info")
    render_workflows_table("azure-billing-workflow", "Azure Billing", show_title=False)
    
    # Cost analysis charts
    render_cost_analysis_charts()
    
    # Performance monitoring - log page load time
    page_load_time = time.time() - page_start_time
    if page_load_time > 5.0:  # Log slow page loads
        SecurityUtils.log_user_action("azure_billing_slow_page_load", {
            "load_time_seconds": round(page_load_time, 2)
        })

def render_configuration_form():
    """Render Azure billing configuration form with credential management"""
    
    with st.expander("Azure Billing Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        # Load existing configuration
        existing_config = WorkflowParameterManager.load_workflow_config()
        
        with col1:
            # Azure credentials with secure handling
            enrollment_number = st.text_input(
                "Azure Enrollment Number",
                value=existing_config.enrollment_number if existing_config else CredentialManager.get_saved_credential("enrollment_number"),
                help="Your Azure Enterprise Agreement enrollment number",
                key="enrollment_number_input"
            )
            
            api_key = st.text_input(
                "Azure API Key",
                type="password",
                value=CredentialManager.get_saved_credential("api_key"),
                help="Your Azure EA API key",
                key="api_key_input"
            )
            
            # Store current form values in session state for extract handler
            st.session_state["current_enrollment_number"] = enrollment_number
            st.session_state["current_api_key"] = api_key
            
            # Persistence options
            persistence_level = st.selectbox(
                "Save Configuration",
                options=["session", "browser", "export"],
                format_func=lambda x: {
                    "session": "Current Session Only",
                    "browser": "Persist in Browser",
                    "export": "Export to File"
                }[x],
                help="Choose how to save your configuration"
            )
            
            save_credentials = st.checkbox(
                "Save credentials securely",
                help="Credentials will be encrypted and stored according to persistence level"
            )
        
        with col2:
            # Date range configuration with persisted values
            default_start = existing_config.start_date if existing_config else get_default_start_date()
            default_end = existing_config.end_date if existing_config else get_default_end_date()
            default_batch = existing_config.batch_size if existing_config else 1000
            
            start_date = st.date_input("Start Date", value=default_start, key="start_date_input")
            end_date = st.date_input("End Date", value=default_end, key="end_date_input")
            
            # Processing parameters
            batch_size = st.number_input(
                "Batch Size",
                min_value=100,
                max_value=10000,
                value=default_batch,
                help="Number of records to process in each batch",
                key="batch_size_input"
            )
            
            # Store current form values in session state for extract handler
            st.session_state["current_start_date"] = start_date
            st.session_state["current_end_date"] = end_date
            st.session_state["current_batch_size"] = batch_size
        
        # Action buttons
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if st.button("Save Configuration"):
                config = AzureBillingConfig(
                    enrollment_number=enrollment_number,
                    api_key=api_key,
                    start_date=start_date,
                    end_date=end_date,
                    batch_size=batch_size,
                    save_credentials=save_credentials
                )
                
                # Validate configuration
                errors = config.validate()
                if errors:
                    # Use consistent error handling pattern
                    error_msg = "Configuration validation failed: " + "; ".join(errors)
                    st.session_state["extract_status_msg"] = error_msg
                    st.session_state["extract_status_type"] = "error"
                    st.session_state["extract_status_time"] = time.time()
                    for error in errors:
                        st.error(f"• {error}")
                else:
                    try:
                        if persistence_level == "export":
                            # Export configuration to file
                            config_json = WorkflowParameterManager.export_config_to_file(config)
                            st.download_button(
                                "Download Configuration",
                                config_json,
                                f"azure_billing_config_{date.today().isoformat()}.json",
                                "application/json"
                            )
                            # Log successful export
                            SecurityUtils.log_user_action("azure_config_exported", {
                                "persistence_level": persistence_level
                            })
                        else:
                            WorkflowParameterManager.save_workflow_config(config, persistence_level)
                            # Use consistent success handling
                            st.session_state["extract_status_msg"] = f"Configuration saved to {persistence_level}!"
                            st.session_state["extract_status_type"] = "success"
                            st.session_state["extract_status_time"] = time.time()
                            # Log successful save
                            SecurityUtils.log_user_action("azure_config_saved", {
                                "persistence_level": persistence_level,
                                "save_credentials": save_credentials
                            })
                    except Exception as e:
                        # Handle any errors during save/export
                        SecurityUtils.track_error(e, "azure_config_save")
                        st.session_state["extract_status_msg"] = f"Failed to save configuration: {str(e)}"
                        st.session_state["extract_status_type"] = "error"
                        st.session_state["extract_status_time"] = time.time()
        
        with col_btn2:
            # Import configuration file
            uploaded_file = st.file_uploader("Import Config", type="json", key="config_import")
            if uploaded_file:
                try:
                    config_content = uploaded_file.read().decode()
                    imported_config = WorkflowParameterManager.import_config_from_file(config_content)
                    if imported_config:
                        # Use consistent success handling
                        st.session_state["extract_status_msg"] = "Configuration imported successfully!"
                        st.session_state["extract_status_type"] = "success"
                        st.session_state["extract_status_time"] = time.time()
                        # Log successful import
                        SecurityUtils.log_user_action("azure_config_imported", {
                            "file_name": uploaded_file.name
                        })
                        st.rerun()
                    else:
                        # Import failed
                        st.session_state["extract_status_msg"] = "Failed to import configuration file"
                        st.session_state["extract_status_type"] = "error"
                        st.session_state["extract_status_time"] = time.time()
                except Exception as e:
                    # Handle import errors
                    SecurityUtils.track_error(e, "azure_config_import")
                    st.session_state["extract_status_msg"] = f"Error importing configuration: {str(e)}"
                    st.session_state["extract_status_type"] = "error"
                    st.session_state["extract_status_time"] = time.time()
        
        with col_btn3:
            if st.button("Test Connection"):
                # Sanitize inputs
                clean_enrollment = SecurityUtils.sanitize_input(enrollment_number) if enrollment_number else ""
                clean_api_key = SecurityUtils.sanitize_input(api_key) if api_key else ""
                
                if clean_enrollment and clean_api_key:
                    # Validate format
                    if not SecurityUtils.validate_enrollment_number(clean_enrollment):
                        st.error("Invalid enrollment number format. Please enter a valid Azure enrollment number.")
                    elif not SecurityUtils.validate_api_key(clean_api_key):
                        st.error("Invalid API key format. Please enter a valid Azure EA API key.")
                    else:
                        # Log user action for monitoring
                        SecurityUtils.log_user_action("azure_connection_test", {
                            "enrollment_number_length": len(clean_enrollment)
                        })
                        test_azure_connection(clean_enrollment, clean_api_key)
                else:
                    st.error("Please enter both enrollment number and API key to test connection")
        
        with col_btn4:
            if st.button("Clear Saved Data"):
                try:
                    WorkflowParameterManager.clear_workflow_config("all")
                    CredentialManager.clear_saved_credentials("all")
                    # Use consistent success handling
                    st.session_state["extract_status_msg"] = "All saved configuration and credentials cleared!"
                    st.session_state["extract_status_type"] = "success"
                    st.session_state["extract_status_time"] = time.time()
                    # Log user action for monitoring
                    SecurityUtils.log_user_action("azure_config_cleared", {"scope": "all"})
                except Exception as e:
                    # Handle any errors during clear
                    SecurityUtils.track_error(e, "azure_config_clear")
                    st.session_state["extract_status_msg"] = f"Failed to clear configuration: {str(e)}"
                    st.session_state["extract_status_type"] = "error"
                    st.session_state["extract_status_time"] = time.time()

def render_summary_metrics(cost_metrics):
    """Render summary metrics cards for Azure billing data following existing pattern"""
    
    # Metric cards following the same pattern as other connector pages
    cols = st.columns(4)
    
    with cols[0]:
        ui.metric_card(
            title="Total Cost",
            content=f"${cost_metrics.get('total_cost', 0):,.2f}",
            key="azure_billing_total_cost"
        )
    
    with cols[1]:
        ui.metric_card(
            title="Resources",
            content=str(cost_metrics.get('resource_count', 0)),
            key="azure_billing_resource_count"
        )
    
    with cols[2]:
        ui.metric_card(
            title="Subscriptions",
            content=str(cost_metrics.get('subscription_count', 0)),
            key="azure_billing_subscription_count"
        )
    
    with cols[3]:
        ui.metric_card(
            title="Last Updated",
            content=cost_metrics.get('last_updated', 'Never'),
            key="azure_billing_last_updated"
        )

def render_billing_data_table():
    """Render interactive Azure billing data table with filters following existing pattern"""
    st.divider()
    
    # Filter controls following existing pattern
    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_filter = st.date_input("Start Date Filter", value=None, key="date_filter_start")
            
        with col2:
            end_filter = st.date_input("End Date Filter", value=None, key="date_filter_end")
        
        with col3:
            subscription_filter = st.selectbox("Subscription", options=["All"] + get_subscription_options())
            resource_group_filter = st.selectbox("Resource Group", options=["All"] + get_resource_group_options())
    
    # Build filters
    filters = {}
    if start_filter:
        filters["start_date"] = start_filter
    if end_filter:
        filters["end_date"] = end_filter
    if subscription_filter != "All":
        filters["subscription_id"] = subscription_filter
    if resource_group_filter != "All":
        filters["resource_group"] = resource_group_filter
    
    # Fetch and display data following existing pattern
    try:
        df = fetch_azure_billing_data(filters, should_throw=False)
        # Transform data for display following existing pattern
        display_df = prepare_azure_billing_display_data(df)
    except Exception as e:
        # Handle any unexpected errors
        SecurityUtils.track_error(e, "azure_billing_data_fetch")
        display_df = pd.DataFrame()
    
    # Show billing table with consistent styling
    title_with_info_icon("Azure Billing Data", "Display all Azure billing records with their metadata and cost information", "azure_billing_table_info")
    
    if display_df is not None and not display_df.empty:
        st.dataframe(display_df, use_container_width=True)
        
        # Export options following existing pattern
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export to CSV"):
                csv = display_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "azure_billing_data.csv", "text/csv")
        
        with col2:
            if st.button("Export to Excel"):
                excel_buffer = io.BytesIO()
                display_df.to_excel(excel_buffer, index=False)
                st.download_button("Download Excel", excel_buffer.getvalue(), "azure_billing_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.write("No Azure billing data available.")

def render_cost_analysis_charts():
    """Render cost analysis charts and visualizations with error handling"""
    st.divider()
    st.subheader("Cost Analysis")
    
    try:
        df = fetch_azure_billing_data(should_throw=False)
        
        if not df.empty and 'extended_cost' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Cost by subscription
                if 'subscription_name' in df.columns:
                    cost_by_subscription = df.groupby('subscription_name')['extended_cost'].sum().sort_values(ascending=False)
                    st.bar_chart(cost_by_subscription)
                    st.caption("Cost by Subscription")
            
            with col2:
                # Cost trend over time
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    cost_trend = df.groupby(df['date'].dt.date)['extended_cost'].sum()
                    st.line_chart(cost_trend)
                    st.caption("Cost Trend Over Time")
            
            # Resource tracking analysis
            if 'resource_tracking' in df.columns:
                st.subheader("Resource Tracking Analysis")
                
                tracked_vs_untracked = df.groupby(df['resource_tracking'].notna())['extended_cost'].sum()
                tracked_vs_untracked.index = ['Untracked', 'Tracked']
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("Tracked Resources Cost", f"${tracked_vs_untracked.get(True, 0):,.2f}")
                    st.metric("Untracked Resources Cost", f"${tracked_vs_untracked.get(False, 0):,.2f}")
                
                with col2:
                    # Simple pie chart using Streamlit's built-in functionality
                    st.bar_chart(tracked_vs_untracked)
                    st.caption("Cost Distribution: Tracked vs Untracked Resources")
    except Exception as e:
        # Handle chart rendering errors gracefully
        SecurityUtils.track_error(e, "azure_billing_chart_render")
        st.info("Cost analysis charts are temporarily unavailable. Please try refreshing the page.")

# Helper functions
def get_default_start_date():
    """Get default start date (30 days ago)"""
    return date.today() - timedelta(days=30)

def get_default_end_date():
    """Get default end date (today)"""
    return date.today()

def get_subscription_options():
    """Get available subscription options"""
    return get_azure_subscription_options()

def get_resource_group_options():
    """Get available resource group options"""
    return get_azure_resource_group_options()

def prepare_azure_billing_display_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform Azure billing data for optimal display"""
    if df.empty:
        return df
    
    # Column transformations
    display_columns = {
        "id": "ID",
        "date": "Date",
        "subscription_name": "Subscription",
        "resource_group": "Resource Group",
        "meter_category": "Service",
        "meter_name": "Meter",
        "consumed_quantity": "Quantity",
        "extended_cost": "Cost ($)",
        "resource_tracking": "Application",
        "cost_center": "Cost Center"
    }
    
    # Format currency columns
    if "extended_cost" in df.columns:
        df["extended_cost"] = df["extended_cost"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
    
    # Format date columns
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    
    # Format quantity columns
    if "consumed_quantity" in df.columns:
        df["consumed_quantity"] = df["consumed_quantity"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "0.00")
    
    # Select and rename columns that exist
    available_columns = {k: v for k, v in display_columns.items() if k in df.columns}
    display_df = df[list(available_columns.keys())].rename(columns=available_columns)
    
    return display_df

# Credential and workflow management classes are now imported from azure_billing_utils

# API functions are now imported from utils.api_functions