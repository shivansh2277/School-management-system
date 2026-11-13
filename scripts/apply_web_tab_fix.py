import os

files = [
    "school-management-system/mobile/app/(teacher)/_layout.tsx",
    "school-management-system/mobile/app/(parent)/_layout.tsx",
    "school-management-system/mobile/app/(student)/_layout.tsx",
]

for f in files:
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        new_content = content.replace("options={{ href: null,", 'options={{ tabBarItemStyle: { display: "none" },')
        with open(f, "w", encoding="utf-8") as fp:
            fp.write(new_content)
        print(f"Updated: {f}")
print("Done!")
