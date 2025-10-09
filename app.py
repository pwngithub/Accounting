# -------------------------------
# DEBUG SECTION — SHOW ROWS 58–60
# -------------------------------
st.markdown("---")
st.header("🧩 Diagnostic View: Rows 58–60")

try:
    # pandas is zero-indexed, so 58–60 are 57–59
    st.write("🔹 Displaying DataFrame rows 58–60 (indexes 57–59):")
    st.dataframe(df.iloc[57:60])
    
    # Optionally print column-by-column values for better clarity
    for idx in range(57, 60):
        row_data = df.iloc[idx]
        st.write(f"Row {idx+1}:")
        for c_idx, val in enumerate(row_data):
            st.write(f" - Column {c_idx} ({df.columns[c_idx]}): {val}")
except Exception as e:
    st.error(f"Error displaying rows 58–60: {e}")
