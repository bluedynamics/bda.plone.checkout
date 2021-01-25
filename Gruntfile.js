module.exports = function (grunt) {
    'use strict';
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        less: {
            dist: {
                options: {
                    paths: [],
                    strictMath: false,
                    sourceMap: true,
                    outputSourceFiles: true,
                    sourceMapURL: '++resource++bda.plone.checkout.css.map',
                    sourceMapFilename: 'src/bda/plone/checkout/browser/checkout.css.map',
                    modifyVars: {
                        "isPlone": "false"
                    }
                },
                files: {
                    'src/bda/plone/checkout/browser/checkout.css': 'src/bda/plone/checkout/browser/checkout.less',
                }
            }
        },
        sed: {
            sed0: {
                path: 'src/bda/plone/checkout/browser/checkout.css.map',
                pattern: 'src/bda/plone/checkout/browser/checkout.less',
                replacement: '++resource++bda.plone.checkout.less',
            }
        },
        watch: {
            scripts: {
                files: ['src/bda/plone/checkout/browser/checkout.less'],
                tasks: ['less', 'sed']
            }
        }
    });
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-sed');
    grunt.registerTask('default', ['watch']);
    grunt.registerTask('compile', ['less', 'sed']);
};
