# --- Develop and public documentation ---
task :builddocs, [:type, :quiet] do |t, args|
    args.with_defaults(:quiet => "quiet")
    verbosity = args.quiet == 'verbose' ? ' --verbose' : ''
    type = args.type ? " --type #{args.type}" : ''
    deprecate_to_invoke(t, args, "docs.builddocs#{type}#{verbosity}")
end

desc "Show docs in browser (mac and ubuntu)."
task :showdocs, [:options] do |t, args|
    type = args.options ? " --type #{args.options}" : ''
    deprecate_to_invoke(t, args, "docs.showdocs#{type}")
end

desc "Build docs and show them in browser"
task :doc, [:type, :quiet] =>  :builddocs do |t, args|
    Rake::Task["showdocs"].invoke(args.type, args.quiet)
end
# --- Develop and public documentation ---
