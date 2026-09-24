import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analyzer.analyze_project import analyze_project
from pathlib import Path
st.set_page_config(
    page_title="CodeArchitect AI",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ CodeArchitect AI")

st.write(
    "AI-powered codebase architecture and change-impact analysis."
)

st.subheader("Repository Analysis")

repo_path = st.text_input(
    "Repository path",
    placeholder="C:/Users/user/Projects/my-project",
)

if repo_path:
    st.info(f"Selected repository: {repo_path}")
    
    changed_module = st.text_input(
        "Changed module (optional)",
        placeholder="src.analyzer.repository_scanner",
    )

    changed_function = st.text_input(
        "Changed function (optional)",
        placeholder="src.analyzer.repository_scanner.find_python_files",
    )
    if changed_function and "." not in changed_function:
        changed_function = (
            f"{changed_module}.{changed_function}"
            if changed_module
            else changed_function
        )
    if st.button("Analyze Repository"):
        with st.spinner("Analyzing repository..."):
            results = analyze_project(
                repo_path,
                changed_module=changed_module or None,
                changed_function=changed_function or None,
            )

        st.success("Analysis completed successfully.")
        st.subheader("Architecture Report")

        st.markdown(results["architecture_report"])
        st.subheader("Dependency Graph")

        graph_path = Path("dependency_graph.html")

        if graph_path.exists():
            st.components.v1.html(
                graph_path.read_text(encoding="utf-8"),
                height=700,
                scrolling=True,
            )
        else:
            st.warning("Dependency graph was not generated.")
            
            
        st.subheader("Call Graph")

        st.write(
            f"Call graph contains "
            f"{len(results['call_graph_nodes'])} functions and "
            f"{len(results['call_graph_edges'])} call relationships."
        )
        st.subheader("Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Python Files", len(results["files"]))
        col2.metric("Modules", results["graph_statistics"]["nodes"])
        col3.metric("Dependencies", results["graph_statistics"]["edges"])
        col4.metric("Call Graph Edges", len(results["call_graph_edges"]))
        
        st.subheader("Architecture Issues")

        if results["architecture_issues"]:
            for issue in results["architecture_issues"]:
                st.warning(
                    f"**{issue['severity'].upper()} — {issue['type']}**\n\n"
                    f"{issue['message']}"
                )
        else:
            st.success("No architecture issues detected.")
            
        
        st.subheader("Potentially Unreferenced Functions")

        if results["unreferenced_functions"]:
            for function in results["unreferenced_functions"]:
                st.info(
                    f"**{function['classification']}**\n\n"
                    f"`{function['function']}`\n\n"
                    f"{function['reason']}"
                )
        else:
            st.success("No potentially unreferenced functions detected.")    
            
            
        st.subheader("Change Impact Analysis")

        if results["impact_analysis"]:
            impact = results["impact_analysis"]

            if "error" in impact:
                st.error(impact["error"])
            else:
                st.write(
                    f"**Directly affected modules:** "
                    f"{impact['summary']['direct_count']}"
            )        

                st.write(
                    f"**Indirectly affected modules:** "
                    f"{impact['summary']['indirect_count']}"
                )

                st.write(
                    f"**Total affected modules:** "
                    f"{impact['summary']['total_affected']}"
                )

                if impact["direct"]:
                    st.write("**Direct impact:**")

                    for item in impact["direct"]:
                        st.info(
                            f"`{item['module']}`\n\n"
                            f"{item['reason']}"
                        )

                if impact["indirect"]:
                    st.write("**Indirect impact:**")

                    for item in impact["indirect"]:
                        st.info(
                            f"`{item['module']}`\n\n"
                            f"{item['reason']}"
                        )

                if "function_impact" in impact:
                    st.write("**Function impact:**")

                    function_impact = impact["function_impact"]

                    for item in function_impact["direct"]:
                        st.info(
                            f"`{item['function']}`\n\n"
                            f"{item['reason']}"
                        )

                    for item in function_impact["indirect"]:
                        st.info(
                            f"`{item['function']}`\n\n"
                            f"{item['reason']}"
                        )
        else:
            st.info("No change impact analysis requested.")                  