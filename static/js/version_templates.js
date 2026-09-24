(() => {
    const packageSelect = document.getElementById("package_id");
    const templateSelect = document.getElementById("version_template");
    const form = packageSelect.form;
    let versions = [];
    let requestNumber = 0;

    async function loadVersions() {
        const currentRequest = ++requestNumber;
        versions = [];
        templateSelect.replaceChildren(new Option("Loading versions...", ""));
        templateSelect.disabled = true;
        const url = new URL(templateSelect.dataset.url, window.location.href);
        url.searchParams.set("format", "version_templates");
        url.searchParams.set("package_id", packageSelect.value);
        try {
            const response = await fetch(url, {headers: {"Accept": "application/json"}});
            if (!response.ok || response.redirected) throw new Error("Could not load versions");
            const data = await response.json();
            if (currentRequest !== requestNumber) return;
            versions = data.versions;
            templateSelect.replaceChildren(new Option("Choose a version...", ""));
            for (const version of versions) {
                const label = [version.VERSION, version.ARCHITECTURE, version.INSTALLER_TYPE,
                    version.INSTALLER_NESTED_TYPE, version.INSTALLER_SCOPE, version.LOCALE,
                    version.CHANNEL].filter(Boolean).join(" · ");
                templateSelect.add(new Option(label, version.UID));
            }
            templateSelect.disabled = versions.length === 0;
        } catch (error) {
            if (currentRequest !== requestNumber) return;
            templateSelect.replaceChildren(new Option("Versions unavailable", ""));
        }
    }

    function setValue(name, value) {
        const field = form.elements.namedItem(name);
        if (!field) return;
        const text = value == null ? "" : String(value);

        if (field.tagName === "SELECT" && !Array.from(field.options).some(option => option.value === text)) {
            field.add(new Option(text, text));
        }
        field.value = text;
    }

    function replaceDependencies(listId, name, values, placeholder) {
        const list = document.getElementById(listId);
        if (!list) return;
        list.replaceChildren();
        for (const value of values.length ? values : [""]) {
            const row = addEntry(listId, name, placeholder);
            row.querySelector("input").value = value;
        }
    }

    templateSelect.addEventListener("change", () => {
        const version = versions.find(item => item.UID === templateSelect.value);
        if (!version) return;
        const locale = Array.from(form.elements.namedItem("package_local").options)
            .find(option => option.textContent.trim() === version.LOCALE);
        if (locale) setValue("package_local", locale.value);
        const fields = {
            channel: "CHANNEL", file_architect: "ARCHITECTURE", upgrades: "UPGRADEBEHAVIOR",
            file_scope: "INSTALLER_SCOPE", productcode: "PRODUCTCODE", upgradecode: "UPGRADECODE",
            package_family_name: "PACKAGE_FAMILY_NAME",
        };
        for (const [name, key] of Object.entries(fields)) setValue(name, version[key]);
        setValue("file_type", (version.INSTALLER_TYPE || "").toUpperCase());
        setValue("file_type_nested", (version.INSTALLER_NESTED_TYPE || "").toUpperCase());
        const nestedPaths = (version.NESTED_FILES || [])
            .map(file => file.RelativeFilePath).filter(Boolean);
        if (document.getElementById("nestedPathContainer")) {
            setNestedPaths(nestedPaths);
        } else {
            setValue("file_nested_path", nestedPaths[0] || "");
        }
        for (const field of form.querySelectorAll('[name^="switch_"]')) {
            field.value = (version.SWITCHES || {})[field.name.slice(7)] || "";
        }
        const dependencies = version.DEPENDENCIES || {};
        replaceDependencies("windowsFeaturesList", "dep_windows_features", dependencies.WINDOWS_FEATURES || [], "z.B. IIS-WebServer");
        replaceDependencies("windowsLibrariesList", "dep_windows_libraries", dependencies.WINDOWS_LIBRARIES || [], "z.B. VC++ Redistributable");
        replaceDependencies("externalDependenciesList", "dep_external", dependencies.EXTERNAL || [], "z.B. Hardware-Driver XY");
        const packageDependenciesList = document.getElementById("packageDependenciesList");
        if (packageDependenciesList) {
            packageDependenciesList.replaceChildren();
            const packageDependencies = dependencies.PACKAGES || [];
            for (const dependency of packageDependencies.length ? packageDependencies : [{}]) {
                const row = addPackageDependency();
                row.querySelector('[name="dep_pkg_identifier"]').value = dependency.PackageIdentifier || "";
                row.querySelector('[name="dep_pkg_min_version"]').value = dependency.MinimumVersion || "";
            }
        }
        document.getElementById("file_type").dispatchEvent(new Event("change"));
    });

    packageSelect.addEventListener("change", loadVersions);
    loadVersions();
})();
